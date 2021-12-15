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
    """Naive player agent

    This agent performs all possible moves in random order
    """

    def __init__(self, player_name, board, players_order, max_transfers):
        """
        Parameters
        ----------
        game : Game
        """
        self.player_name = player_name
        self.players_order = players_order
        self.logger = logging.getLogger('AI')
        self.max_transfers = max_transfers
        self.turn_time = 0.1
        self.turn_state = "transfer"
        self.max_depth = 4
        self.ify = 0
        
    def get_all_borders_info(self, board):
        borders = board.get_player_border(self.player_name)

        borders_info = []

        for area in borders:
            neighbourhood_names = area.get_adjacent_areas_names()

            enemies = []
            for neighbour_name in neighbourhood_names:
                neighbour = board.get_area(neighbour_name)
                if(neighbour.get_owner_name() != self.player_name):
                    enemies.append([neighbour, neighbour.get_dice(), neighbour.get_owner_name(), (area.get_dice() - neighbour.get_dice())])
            borders_info.append([area, area.get_dice(), enemies])
        return borders_info

    def get_board_evaluation(self, board, player_name):
        regions = board.get_players_regions(player_name)
        biggest_region = max(regions, key=len)

        count_of_areas_outside_the_biggest_region = 0
        for region in regions:
            areas_out_of_biggest_region = [x for x in region if x not in biggest_region]
            count_of_areas_outside_the_biggest_region += len(areas_out_of_biggest_region)

        count_of_player_areas = len(board.get_player_areas(self.player_name))

        borders_info = self.get_all_borders_info(board)
        weak_borders = []
        weak_enemies = []

        for border in borders_info:
            for enemy in border[2]:
                if(enemy[3] < -2):
                    weak_borders.append([border, enemy])
                if(enemy[3] > 1 or (enemy[1] == 8 and border[1] == 8)):
                    weak_enemies.append([border, enemy])
                
        return [count_of_player_areas, biggest_region, borders_info, weak_borders, weak_enemies]

    def get_best_turn(self, board, board_evaluation):
        attacks = []
        for weak_enemy_turn in board_evaluation[4]:
            player_border_area = weak_enemy_turn[0][0]

            for enemy in weak_enemy_turn[0][2]:
                enemy = enemy[0]
                hold_prob = probability_of_holding_area(board, enemy.get_name(), (weak_enemy_turn[0][1] - 1), self.player_name)
                succ_prob = probability_of_successful_attack(board, player_border_area.get_name(), enemy.get_name())
                attacks.append([player_border_area, enemy, hold_prob, succ_prob])
        
        return attacks
    
    def get_nearest_possible_transfer_neighbors(self, area, board, remaining_transfers, already_visited_areas, tree_node):
        if(remaining_transfers <= 0):
            return

        visited = already_visited_areas + []
        for neighbour_name in area.get_adjacent_areas_names():
            neighbour = board.get_area(neighbour_name)
            if((neighbour.get_owner_name() == self.player_name) and (neighbour not in board.get_player_border(self.player_name))):
                if(neighbour not in visited):
                    name = str(neighbour_name) + str(random.randint(0, 50000)) + str(random.randint(0, 40000)) + str(random.randint(0, 150000))
                    self.transfer_tree.create_node([neighbour_name, neighbour.get_dice()], name, parent=tree_node)  
                    visited.append(neighbour)
                    self.get_nearest_possible_transfer_neighbors(neighbour, board, remaining_transfers - 1, visited, name)

    def next_player(self, current_player):
        i = 0
        for index, player in enumerate(self.players_order):
            if(player == current_player):
                i = index
        
        i = i + 1
        return self.players_order[i % len(self.players_order)]
    
    def possible_moves(self, player, board):
        attacks = list(possible_attacks(board, player))

        moves = [[board, []]]
        treshold = 0.2
        
        for attack in attacks:
            source = attack[0]
            enemy = attack[1]
            
            enemy_dice = enemy.get_dice()
            source_dice = source.get_dice()

            if(source_dice == 1):
                continue
            if(source_dice == 8):
                hold_prob = 1
                succ_prob = 1
                # prob = 1
            else:
                hold_prob = probability_of_holding_area(board, enemy.get_name(), (source_dice - 1), player)
                succ_prob = probability_of_successful_attack(board, source.get_name(), enemy.get_name())
                # prob = (0.3 * hold_prob) + (0.7 * succ_prob)
            
            # if(prob >= treshold):
            if(hold_prob >= 0.3 and succ_prob >= 0.5): #tohle je zatim asi nejlepsi podminka
                board = copy.deepcopy(board)
                enemy.set_owner(source.get_owner_name())
                enemy.set_dice(source_dice - 1)
                source.set_dice(1)

                moves.append([board, [source, enemy, player]])

        return moves
            
    def is_current_better_than_best(self, currentVector, bestVector, player):
        
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
        if(depth == self.max_depth):
            return self.eval_func(board)
        
        possible_moves = self.possible_moves(player, board)
        next_player = self.next_player(player)
        
        bestValVector = {}

        for i in range(len(self.players_order)):
            bestValVector[self.players_order[i]] = 0
            # if(self.players_order[i] == player):
            #     bestValVector[self.players_order[i]] = 0
            # else:
            #     bestValVector[self.players_order[i]] = 1000
        
        currentValVector = {}

        for possible_move in possible_moves:
            currentValVector = self.maxN(next_player, depth + 1, possible_move[0])
            if self.is_current_better_than_best(currentValVector, bestValVector, player):
                self.ify += 1
                bestValVector = currentValVector
                best_posible_move = possible_move[1]

        if depth == 0:
            return best_posible_move
        else:
            return bestValVector

    def eval_func(self, board):
        boardEvaluation = {}
        for player in self.players_order:
            evalArray = self.get_board_evaluation(board, player)
            v = 0.5
            w = 0.55
            x = 0.3
            y = 0.4

            eval = v * evalArray[0] + w * len(evalArray[1]) - x * len(evalArray[3]) + y * len(evalArray[4])
            #eval = v * player_areas + w * player_biggest_region - x * weak_boarders + y * weak_enemies

            boardEvaluation[player] = eval

        return boardEvaluation

    def ai_turn(self, board, nb_moves_this_turn, nb_transfers_this_turn, nb_turns_this_game, time_left):
        """AI agent's turn

        Get a random area. If it has a possible move, the agent will do it.
        If there are no more moves, the agent ends its turn.
        """
               
        if(self.turn_state == "transfer"):
            skiped = 0
            number_of_borders = len(board.get_player_border(self.player_name))
            if(nb_transfers_this_turn == self.max_transfers):
                #print("TRANSFER IF")
                self.turn_state = "attack"
            else:
                #print("TRANSFER ELSE")

                borders = board.get_player_border(self.player_name)
                borders_with_dices = []
                for area in borders:
                    borders_with_dices.append([area, area.get_dice()])

                borders_with_dices.sort(key=lambda x:x[1])
                for i, area in enumerate(borders_with_dices):
                    if(area[0].get_dice() >= 7):
                        skiped += 1
                        if(skiped == number_of_borders or i == (len(borders_with_dices) - 1)):
                            self.turn_state = "attack"
                            break
                        continue
                    already_visited_areas = [area[0]]

                    self.transfer_tree = Tree()
                    self.transfer_tree.create_node([area[0].get_name(), area[0].get_dice()], area[0].get_name())

                    self.get_nearest_possible_transfer_neighbors(area[0], board, (self.max_transfers - nb_transfers_this_turn), already_visited_areas, area[0].get_name())

                    #self.transfer_tree.show()      

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
                        #print("TRANSFER")
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
                        #print("TRANSFER")
                        return TransferCommand(finalNode.tag[0], parent.tag[0])
                    else:
                        self.turn_state = "attack"

        if(self.turn_state == "attack"):
            move = self.maxN(self.player_name, 0, board)
            if not move:
                #print("END")
                self.turn_state = "transfer"
                return EndTurnCommand()
            else:
                #print("ATTACK")
                self.turn_state = "transfer"
                return BattleCommand(move[0].get_name(), move[1].get_name())
        # print('28: ' + str(self.ify))
        return EndTurnCommand()
