import random
import logging

from dicewars.ai.utils import possible_attacks, probability_of_successful_attack, probability_of_holding_area, save_state

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
        
        #result = board_evaluation[0] + len(board_evaluation[1]) + len(board_evaluation[4][0][0][2]) - len(board_evaluation[3]) - (board_evaluation[0] - len([board_evaluation[1]]))
        #print(result)

        return attacks
    
    def get_nearest_possible_transfer_neighbors(self, area, board, remaining_transfers, already_visited_areas, tree_node):
        if(remaining_transfers < 0):
            return

        visited = already_visited_areas + []

        for neighbour_name in area.get_adjacent_areas_names():
            neighbour = board.get_area(neighbour_name)
            if((neighbour.get_owner_name() == self.player_name) and (neighbour not in board.get_player_border(self.player_name))):
                if(neighbour not in visited):
                    name = str(neighbour_name) + str(random.randint(0, 100))
                    self.transfer_tree.create_node([neighbour_name, neighbour.get_dice()], name, parent=tree_node)                
                    visited.append(neighbour)
                    self.get_nearest_possible_transfer_neighbors(neighbour, board, remaining_transfers - 1, visited, name)

    def ai_turn(self, board, nb_moves_this_turn, nb_transfers_this_turn, nb_turns_this_game, time_left):
        """AI agent's turn

        Get a random area. If it has a possible move, the agent will do it.
        If there are no more moves, the agent ends its turn.
        """
        
        """board.get_player_areas()
        board.get_player_border()

        board.get_players_regions()

        area.get_adjacent_areas_names()
        area.get_owner_name()
        area.get_dice()

        dicewars.ai.utils.possible_attacks()"""

        borders = board.get_player_border(self.player_name)
        
        already_visited_areas = [borders[0]]

        self.transfer_tree = Tree()
        self.transfer_tree.create_node([borders[0].get_name(), borders[0].get_dice()], borders[0].get_name())

        with open('debug.save', 'wb') as f:
            save_state(f, board, self.player_name, self.players_order)

        self.get_nearest_possible_transfer_neighbors(borders[0], board, (self.max_transfers - nb_transfers_this_turn), already_visited_areas, borders[0].get_name())

        print("\n================================================================")

        self.transfer_tree.show()

        return EndTurnCommand()

        board_evaluation = []

        board_evaluation = self.get_board_evaluation(board, self.player_name)
        if(self.turn_state == "transfer"):
            if(len(board_evaluation[3]) == 0):
                self.turn_state = "attack"
            for area in board_evaluation[3]:
                if(nb_transfers_this_turn >= self.max_transfers):
                    self.turn_state = "attack"
                    break
                neighbourhood_names = area[0][0].get_adjacent_areas_names()
                for neighbour_name in neighbourhood_names:
                    neighbour = board.get_area(neighbour_name)
                    if(neighbour.get_owner_name() == self.player_name 
                    and nb_transfers_this_turn < self.max_transfers 
                    and neighbour.get_dice() > 1 
                    and neighbour not in board.get_player_border(self.player_name)):
                        self.turn_state = "transfer"
                        return TransferCommand(neighbour_name, area[0][0].get_name())
            self.turn_state = "attack"
        if(self.turn_state == "attack"):

            if(len(board_evaluation[4]) == 0):
                self.turn_state = "transfer"

            #if(time_left < self.supposed_turn_time):
            #    print('end')
            #    return EndTurnCommand()
            else:
                best_attacks = self.get_best_turn(board, board_evaluation)

                best_attack = [0, 0, 0, 0]
                for possible_attack in best_attacks:
                    if(possible_attack[2] > 0.2):
                        if(best_attack[3] < possible_attack[3]):
                            best_attack[0] = possible_attack[0]
                            best_attack[1] = possible_attack[1]
                            best_attack[2] = possible_attack[2]
                            best_attack[3] = possible_attack[3]
                if(best_attack[0] == 0):
                    return EndTurnCommand()
                else:
                    return BattleCommand(best_attack[0].get_name(), best_attack[1].get_name())
            #MAN_X
        return EndTurnCommand()
#
        #all_attacks = list(possible_attacks(board, self.player_name))
        #for attack in all_attacks:
        #    attacker, defender = attack
        #    attacker_advantage = attacker.get_dice() - defender.get_dice()
#
        #    if(attacker.get_dice() == 8 or attacker_advantage >= 2):
        #        return BattleCommand(attacker.get_name(), defender.get_name())
        #
        #borders = board.get_player_border(self.player_name)
        #for area in borders:
        #    if(nb_transfers_this_turn >= self.max_transfers):
        #        break
        #    neighbourhood_names = area.get_adjacent_areas_names()
        #    for neighbour_name in neighbourhood_names:
        #        neighbour = board.get_area(neighbour_name)
        #        
        #        if(neighbour.get_owner_name() == self.player_name and nb_transfers_this_turn < self.max_transfers and neighbour.get_dice() > 2 and neighbour not in borders):
        #            return TransferCommand(neighbour_name, area.get_name())
