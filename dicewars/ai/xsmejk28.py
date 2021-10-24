import random
import logging

from dicewars.ai.utils import possible_attacks

from dicewars.client.ai_driver import BattleCommand, EndTurnCommand, TransferCommand

from dicewars.client.game.board import *

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

    def get_all_borders_info(self, board):
        borders = board.get_player_border(self.player_name)

        borders_info = []

        for area in borders:
            neighbourhood_names = area.get_adjacent_areas_names()

            enemies = []
            for neighbour_name in neighbourhood_names:
                neighbour = board.get_area(neighbour_name)
                if(neighbour.get_owner_name() != self.player_name):
                    enemies.append([neighbour,  neighbour.get_dice(), neighbour.get_owner_name(), (area.get_dice() - neighbour.get_dice())])
            borders_info.append([area, area.get_dice(), enemies])
        
        return borders_info

    def get_border_evaluation(self, board, player_name):
        regions = board.get_players_regions(player_name)
        biggest_region = max(regions, key=len)
        biggest_region_len = len(biggest_region)

        count_of_areas_outside_the_biggest_region = 0
        for region in regions:
            areas_out_of_biggest_region = [x for x in region if x not in biggest_region]
            count_of_areas_outside_the_biggest_region += len(areas_out_of_biggest_region)

        count_of_player_areas = len(board.get_player_areas(self.player_name))

        borders_info = self.get_all_borders_info(board)
        weak_borders = []
        weak_enemies = []

        for border in borders_info:
            print(border)
            for enemy in border[2]:
                print(enemy)
                if(enemy[3] < -2):
                    weak_borders.append([border, enemy])
                if(enemy[3] > 2):
                    weak_enemies.append([border, enemy])
                
        return [count_of_player_areas, biggest_region, borders_info, weak_borders, weak_enemies]

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
        
        #for info in borders_info:
        #    print(info)
        #    print('----------------------------------')

        self.get_border_evaluation(board, self.player_name)
            
        #for area in borders:
        #    if(nb_transfers_this_turn >= self.max_transfers):
        #        break
        #    neighbourhood_names = area.get_adjacent_areas_names()
        #    for neighbour_name in neighbourhood_names:
        #        neighbour = board.get_area(neighbour_name)
        #        
        #        if(neighbour.get_owner_name() == self.player_name and nb_transfers_this_turn < self.max_transfers and neighbour.get_dice() > 2 and neighbour not in borders):
        #            return TransferCommand(neighbour_name, area.get_name())
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

        return EndTurnCommand()
