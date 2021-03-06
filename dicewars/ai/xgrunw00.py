import random
import logging
import copy
from random import shuffle

from dicewars.ai.utils import *

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand, TransferCommand

from dicewars.client.game.board import *
from dicewars.client.game.area import *
from treelib import Node, Tree

class AI:
    """
        Parameters
        ----------
        game : Game
        player_name : Current player name
        players_order : Array with players order
        logger : Logger instance
        max_transfers : Max allowed transfers for players turn
        turn_state : FSA state for the AI, starts with transfer every turn
        max_depth : Max depth that the Max N will go into 
        escape_transfers : Number of transfers reserved for escape phase
    """

    def __init__(self, player_name, board, players_order, max_transfers):
        """Initialization of the class parameters
        """
        self.player_name = player_name
        self.players_order = players_order
        self.logger = logging.getLogger('AI')
        self.max_transfers = max_transfers
        self.turn_state = "transfer"
        self.max_depth = 4
        self.escape_transfers = 1

    def get_all_borders_info(self, board):
        """Get info about all borders and enemies on the borders

        Args:
            board : instance of a game board

        Returns:
            array of borders that belongs to the AI player and enemy areas adjacent to them with a dice advantages
        """
        borders = board.get_player_border(self.player_name)
        borders_info = []

        for area in borders:
            neighbourhood_names = area.get_adjacent_areas_names()

            enemies = []
            for neighbour_name in neighbourhood_names:
                neighbour = board.get_area(neighbour_name)

                # Append enemy to final array
                if(neighbour.get_owner_name() != self.player_name):
                    enemies.append([neighbour, neighbour.get_dice(), neighbour.get_owner_name(), (area.get_dice() - neighbour.get_dice())])
            borders_info.append([area, area.get_dice(), enemies])
        return borders_info

    def get_board_evaluation(self, board, player_name):
        """Get all information for evaluation of board state for specified player

        Args:
            board : instance of a game board
            player_name : name of the player for whom to get the evaluation

        Returns:
            array with information about the current board state for the given player
        """

        regions = board.get_players_regions(player_name)

        # Get the biggest region
        biggest_region = max(regions, key=len)

        # Get number of player areas        
        count_of_player_areas = len(board.get_player_areas(self.player_name))

        # Get basic border info
        borders_info = self.get_all_borders_info(board)
        weak_borders = []
        weak_enemies = []

        # Get weak enemies (dice advantage is greater than 1 or there are 8 dice on border and enemy) and weak borders (dice advantage is greater than 2)
        for border in borders_info:
            for enemy in border[2]:
                if(enemy[3] < -2):
                    weak_borders.append([border, enemy])
                if(enemy[3] > 1 or (enemy[1] == 8 and border[1] == 8)):
                    weak_enemies.append([border, enemy])
                
        return [count_of_player_areas, biggest_region, borders_info, weak_borders, weak_enemies]
   
    def get_nearest_possible_transfer_neighbors(self, area, board, remaining_transfers, already_visited_areas, tree_node):
        """Recursive method called for each area to get neighbors for the tree of transfers

        Args:
            area : current area
            board : instance of the game board
            remaining_transfers : number of remaining transfers in the turn
            already_visited_areas : array to prevent loops
            tree_node : parent node in tree (neighbor that called this method)
        """

        # No more transfers, end recursion
        if(remaining_transfers <= 0):
            return

        # Prevent loops with this array
        visited = already_visited_areas + []

        # Go through every neighbor
        for neighbour_name in area.get_adjacent_areas_names():
            neighbour = board.get_area(neighbour_name)

            # Check if the neighbor belongs to the player and that is not on the border
            if((neighbour.get_owner_name() == self.player_name) and (neighbour not in board.get_player_border(self.player_name))):
                # Prevent loops by checking if the area was visited already
                if(neighbour not in visited):
                    # Generate random name (one area can be in the tree multiple times but names can't be the same)
                    name = str(neighbour_name) + str(random.randint(0, 50000)) + str(random.randint(0, 40000)) + str(random.randint(0, 150000))
                    # Create new node in the tree
                    self.transfer_tree.create_node([neighbour_name, neighbour.get_dice()], name, parent=tree_node)  
                    # Add the area to the visited array to prevent loops
                    visited.append(neighbour)
                    # Recursive call for another neighbors
                    self.get_nearest_possible_transfer_neighbors(neighbour, board, remaining_transfers - 1, visited, name)

    def next_player(self, current_player):
        """Get the next player in line

        Args:
            current_player : name of the player that is on turn now

        Returns:
            name of the next player in line that will be on turn
        """
        i = 0
        for index, player in enumerate(self.players_order):
            if(player == current_player):
                i = index
        
        i = i + 1
        return self.players_order[i % len(self.players_order)]
    
    def possible_moves(self, player, board):
        """Simulates all possible moves and append it to the final array based on success and hold probability

        Args:
            player : player that is on turn
            board : current board instance

        Returns:
            array of arrays - each array contains the board instance and the turn that should be done
        """
        attacks = list(possible_attacks(board, player))

        moves = [[board, []]]
        
        for attack in attacks:
            source = attack[0]
            enemy = attack[1]
            
            source_dice = source.get_dice()

            if(source_dice == 1):
                continue
            if(source_dice == 8):
                hold_prob = 1
                succ_prob = 1
            else:
                hold_prob = probability_of_holding_area(board, enemy.get_name(), (source_dice - 1), player)
                succ_prob = probability_of_successful_attack(board, source.get_name(), enemy.get_name())
            
            if(hold_prob >= 0.3 and succ_prob >= 0.5):
                board = copy.deepcopy(board)
                enemy.set_owner(source.get_owner_name())
                enemy.set_dice(source_dice - 1)
                source.set_dice(1)

                moves.append([board, [source, enemy, player]])

        return moves
            
    def is_current_better_than_best(self, currentVector, bestVector, player):
        """Method that just decides if the current state is better than the best one

        Args:
            currentVector : vector with current board evaluation for each player
            bestVector : vector with the best board evaluation for each player (discovered earlier)
            player : player for whom the current state should be better

        Returns:
            True if the current state is better than the best. False if the best is better.
        """
        
        enemyScore = 0
        playerScore = 0

        for key, value in currentVector.items():            
            if(key == player):
                playerScore = value
            else:
                enemyScore += value
        currentVectorEvaluation = enemyScore - playerScore

        enemyScore = 0
        for key, value in bestVector.items():            
            if(key == player):
                playerScore = value
            else:
                enemyScore += value
        bestVectorEvaluation = enemyScore - playerScore

        if(currentVectorEvaluation <= bestVectorEvaluation):
            return True
        else:
            return False

    def maxN(self, player, depth, board):
        """Implementation of MaxN algorithm that finds the best attack for the current turn. Recursive method.

        Args:
            player : player name for whom to find the best attack
            depth : max depth of MaxN tree
            board : current board instance

        Returns:
            If it is not in the root (first call of this method) it returns vector with best possible values. 
            If it is in the root it returns best possible attack for the agent to execute.
        """
        if(depth == self.max_depth):
            return self.eval_func(board)
        
        possible_moves = self.possible_moves(player, board)
        next_player = self.next_player(player)
        
        bestValVector = {}

        for i in range(len(self.players_order)):
            bestValVector[self.players_order[i]] = 0
                    
        currentValVector = {}

        for possible_move in possible_moves:
            currentValVector = self.maxN(next_player, depth + 1, possible_move[0])
            if self.is_current_better_than_best(currentValVector, bestValVector, player):
                bestValVector = currentValVector
                best_posible_move = possible_move[1]

        if depth == 0:
            return best_posible_move
        else:
            return bestValVector

    def eval_func(self, board):
        """Function that evaluates the current board state

        Args:
            board : board instance that should be evaluated

        Returns:
            number that represents the evaluation of the board instance
        """
        boardEvaluation = {}
        for player in self.players_order:
            evalArray = self.get_board_evaluation(board, player)
            player_areas_weight = 0.5
            biggest_region_weight = 0.55
            weak_borders_weight = 0.3
            weak_enemies_weight = 0.4

            eval = player_areas_weight * evalArray[0] + biggest_region_weight * len(evalArray[1]) - weak_borders_weight * len(evalArray[3]) + weak_enemies_weight * len(evalArray[4])
            boardEvaluation[player] = eval

        return boardEvaluation

    def escape(self, board):
        """Function that decides the best escape transfer from the borders

        Args:
            board : board instance that should be evaluated

        Returns:
            None if there is no appropriate escape transfer. 
            List of source and destination area for transfer command.
        """
        borders = board.get_player_border(self.player_name)
        borders_with_dices = []
        for area in borders:
            borders_with_dices.append([area, area.get_dice()])

        # sort border areas by number of dices
        borders_with_dices.sort(key=lambda x:x[1])

        possible_escapes = []
        for area in borders_with_dices:
            if(area[0].get_dice() == 1):
                continue
            player_adj_areas = []
            for adj_area_name in area[0].get_adjacent_areas_names():
                player_areas = board.get_players_regions(self.player_name)
                own_a = False
                # if adj_area is player's area -> own_a = True
                for i in player_areas:
                    if adj_area_name in i:
                        own_a = True
                if(own_a):
                    adj_area = board.get_area(adj_area_name)
                    # if there is free capacity to move dices to adj_area
                    if(adj_area.get_dice() + (adj_area.get_dice() - 1) <= 8):
                        player_adj_areas.append([adj_area, adj_area.get_dice()])
            # no area to move dices -> continue
            if(not player_adj_areas):
                continue
            # sort areas by number of dices
            player_adj_areas.sort(key=lambda x:x[1])
            hold_p = probability_of_holding_area(board, area[0].get_name(), area[0].get_dice(), self.player_name)
            # if hold prob is less than 0.3 append([number of dices on area, area name, adjacent area for transfer, hold prob])
            if(hold_p < 0.3):
                possible_escapes.append([area[0].get_dice(), area[0].get_name(), player_adj_areas[0][0].get_name(), hold_p])
        # no espace transfer found
        if(not possible_escapes):
            return None

        # sort by hold prob
        possible_escapes.sort(key=lambda x:x[3])

        # if possible_escapes contains more than 1 element 
        # compare first two possible escapes and transfer the one with more dices
        if(len(possible_escapes) > 1 and possible_escapes[0][0] < possible_escapes[1][0]):
            return [possible_escapes[1][1], possible_escapes[1][2]]
        else:
            return [possible_escapes[0][1], possible_escapes[0][2]]

    def ai_turn(self, board, nb_moves_this_turn, nb_transfers_this_turn, nb_turns_this_game, time_left):
        """AI agent's turn
           
           Simple FSA that always starts at transfer state. After transfers are done FSA goes into the attack state.
           After attacks are done FSA turns into escape state.
           This method uses previously declared methods to decide.
        
        """
               
        if(self.turn_state == "transfer"):
            skiped = 0
            number_of_borders = len(board.get_player_border(self.player_name))
            if(nb_transfers_this_turn >= self.max_transfers - self.escape_transfers):
                self.turn_state = "attack"
            else:
                borders = board.get_player_border(self.player_name)
                borders_with_dices = []
                for area in borders:
                    borders_with_dices.append([area, area.get_dice()])

                borders_with_dices.sort(key=lambda x:x[1])
                for i, area in enumerate(borders_with_dices):
                    if(area[0].get_dice() >= 7):
                        skiped += 1
                        if(skiped == number_of_borders):
                            self.turn_state = "attack"
                            break
                        continue
                    already_visited_areas = [area[0]]

                    self.transfer_tree = Tree()
                    self.transfer_tree.create_node([area[0].get_name(), area[0].get_dice()], area[0].get_name())
                    
                    self.get_nearest_possible_transfer_neighbors(area[0], board, min(self.max_transfers - self.escape_transfers,self.max_transfers - nb_transfers_this_turn), already_visited_areas, area[0].get_name())
                    
                    max = area[0].get_dice()
                    steps = 10000
                    finalId = None
                    finalNode = None

                    if(self.transfer_tree.depth() == 1):
                        nodes_in_depth = list(self.transfer_tree.filter_nodes(lambda x: self.transfer_tree.depth(x) == 1))

                        max = area[0].get_dice()
                        for node in nodes_in_depth:
                            if(node.tag[1] + area[0].get_name() > max):
                                max = (node.tag[1] - 1) + area[0].get_name()
                                finalId = node.identifier
                                finalNode = node
                        if(finalNode == None):
                            self.turn_state = "attack"
                            break
                        return TransferCommand(finalNode.tag[0], self.transfer_tree.get_node(self.transfer_tree.root).tag[0])
                    for i in range(1, self.transfer_tree.depth()):
                        nodes_in_depth = list(self.transfer_tree.filter_nodes(lambda x: self.transfer_tree.depth(x) == i))

                        for node in nodes_in_depth:
                            if((((node.tag[1] - 1) + area[0].get_dice()) > max) or (i < steps and (node.tag[1] + area[0].get_dice() == max))):
                                max = (node.tag[1] - 1) + area[0].get_dice()
                                steps = i
                                finalId = node.identifier
                                finalNode = node

                    if(max == 1):
                        continue
                    if(finalId != None):
                        parent = self.transfer_tree.parent(finalId)
                    else:
                        parent = None
                    
                    if(finalNode != None and parent != None):
                        return TransferCommand(finalNode.tag[0], parent.tag[0])
                    else:
                        self.turn_state = "attack"

        if(self.turn_state == "attack"):
            move = self.maxN(self.player_name, 0, board)
            if not move:
                self.turn_state = "escape"
            else:
                self.turn_state = "transfer"
                return BattleCommand(move[0].get_name(), move[1].get_name())

        if(self.turn_state == "escape" and nb_transfers_this_turn < self.max_transfers):
            es = self.escape(board)
            if es:
                self.turn_state = "transfer"
                return TransferCommand(es[0], es[1])
            

        self.turn_state = "transfer"
        return EndTurnCommand()