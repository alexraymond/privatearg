import subprocess
import string
import re
import random
import copy
import scipy.stats as stats
import logging, sys
import numpy as np

from utils import *
from enum import Enum
from private_culture import RandomCulture

class Agent:
    def __init__(self, id, max_privacy_budget = 10):
        self.id = id
        self.properties = {}
        self.culture = None
        self.max_privacy_budget = max_privacy_budget
        self.privacy_budget = self.max_privacy_budget
        self.argued_with = []
        self.unfair_perception_score = 0

    def reset_privacy_budget(self):
        self.privacy_budget = self.max_privacy_budget

    def set_culture(self, culture):
        self.culture = culture
        self.properties = self.culture.properties.copy()

        # Randomise values for random culture.
        if isinstance(self.culture, RandomCulture):
            for key, value in self.properties.items():
                self.properties[key] = random.randint(0, 100)

    def has_argued_with(self, agent_id):
        return agent_id in self.argued_with

class ArgStrategy(Enum):
    RANDOM_CHOICE_NO_PRIVACY = 1
    RANDOM_CHOICE_PRIVATE = 2
    GREEDY_MIN_PRIVACY = 3
    LEAST_ATTACKERS_PRIVATE = 4
    LEAST_ATTACKERS_NO_PRIVACY = 5
    COUNT_OCCURRENCES_ADMISSIBLE_RELATIVE = 6
    ALL_ARGS = 7


class AgentQueue:
    TOTAL_YES = 0
    TOTAL_NO = 0
    TOTAL_BAD = 0
    def __init__(self, strategy: ArgStrategy, size = 30, privacy_budget = 10):
        self.queue = []
        self.size = size
        self.culture = RandomCulture()
        self.init_queue(privacy_budget)
        self.strategy = strategy
        self.bw_framework = None
        self.rate_local_unfairness = 0

    def set_strategy(self, strategy):
        self.strategy = strategy

    def init_queue(self, privacy_budget):
        for i in range(self.size):
            new_agent = Agent(i, max_privacy_budget=privacy_budget)
            new_agent.set_culture(self.culture)
            self.queue.append(new_agent)

    def queue_string(self):
        text = ""
        for agent in self.queue:
            text += str(agent.id) + " "
        return text

    def compute_ground_truth(self):
        """
        Computes the ground truth by removing all unverified arguments from BW framework
        and calculating skeptical acceptance of motion.
        :return: Sorted ground truth.
        """
        ground_truth = copy.deepcopy(self)
        ground_truth.bw_framework = ground_truth.create_bw_framework()
        status_quo = {}
        for i in range(0, len(ground_truth.queue)-1):
            for j in range(i, len(ground_truth.queue)):
                if i == j:
                    continue
                defender = ground_truth.queue[i]
                challenger = ground_truth.queue[j]
                bw_framework = copy.deepcopy(ground_truth.bw_framework)

                to_remove = []
                for argument_id in bw_framework.all_arguments:
                    argument_obj = bw_framework.argument(argument_id)
                    if is_black_arg(argument_id):
                        verified = argument_obj.verify(defender, challenger)
                    else:
                        verified = argument_obj.verify(challenger, defender)
                    if not verified:
                        to_remove.append(argument_id)
                        # if is_verified_arg(argument_id):
                        #     to_remove.append(argument_id - 2)

                for argument_id in to_remove:
                    bw_framework.remove_argument(argument_id)


                solver_result = bw_framework.run_solver(semantics="DS-PR", arg_str="1")
                if "YES" in solver_result:
                    # Challenger wins.
                    attackers_of_1 = bw_framework.arguments_that_attack(1)
                    pair = (defender.id, challenger.id)
                    anti_pair = (challenger.id, defender.id)
                    self.TOTAL_YES += 1
                elif "NO" in solver_result:
                    # Defender wins.
                    attackers_of_1 = bw_framework.arguments_that_attack(1)
                    pair = (challenger.id, defender.id)
                    anti_pair = (defender.id, challenger.id)
                    self.TOTAL_NO += 1
                else:
                    print("Error computing extensions")

                status_quo[pair] = False
                status_quo[anti_pair] = True

        # Get queue order.
        swaps = ground_truth.interact_all(gt_result=status_quo)
        print("Ground truth: {}".format(ground_truth.queue_string()))
        print("GT Swaps: {}".format(swaps))
        print("Total yes: {}\nTotal no: {}".format(self.TOTAL_YES, self.TOTAL_NO))
        return ground_truth, self.TOTAL_YES, swaps


    def relative_queue(self, ground_truth):
        """
        Prints a queue with ids relative to a ground truth queue.
        :param ground_truth: The queue representing the ground truth.
        :return: Relative queue, Kendall's tau (1 indicates strong agreement), and p-value
        """
        base_dict = {}
        ground_truth_ids = []
        relative_ids = []
        i = 0
        for agent in ground_truth.queue:
            base_dict[agent.id] = i
            ground_truth_ids.append(i)
            i += 1
        text = ""
        for agent in self.queue:
            # text += str(base_dict[agent.id]) + " "
            text += str(agent.id) + " "
            relative_ids.append(base_dict[agent.id])
        tau, p = stats.kendalltau(ground_truth_ids, relative_ids)
        return text, tau, p

    def interact_all(self, gt_result = None):
        """
        Agents will interact with their neighbours.
        Considering the queue ordering, every agent will attempt to move towards index 0.
        This function will force agents to interact in a pairwise manner, in two different scan patterns.
        If the higher-index agent wins the dialogue game, they swap places.
        First scan pattern: indices k-1 and k interact for k > 0
        Second scan pattern: indices k and k+1 interact for k > 0

        This function shall return iff no exchanges take place after two consecutive scans.
        """

        logging.debug(self.queue_string())
        stable_queue = False
        self.bw_framework = self.create_bw_framework()
        interaction_count = 0
        swaps = 0
        while not stable_queue:
            stable_queue = True

            for scan in range(2):
                for i in range(1, self.size, 2):
                    i += scan
                    if i >= len(self.queue):
                        break
                    if gt_result is None:
                        status_quo = self.interact_pair(self.queue[i-1], self.queue[i])
                    else:
                        status_quo = gt_result[self.queue[i-1].id, self.queue[i].id]
                    interaction_count += 1
                    if not status_quo:
                        # Then swap.
                        self.queue[i-1], self.queue[i] = self.queue[i], self.queue[i-1]
                        swaps += 1
                        stable_queue = False
                    logging.debug(self.queue_string())
        aggregate_local_unfairness = 0
        for agent in self.queue:
            aggregate_local_unfairness += agent.unfair_perception_score
        self.rate_local_unfairness = aggregate_local_unfairness / interaction_count
        return swaps



    def create_bw_framework(self):
        """
        Prunes unverified arguments out of a black-and-white framework.
        :param defender: Agent representing black arguments.
        :param challenger: Agent representing white arguments.
        :return: Black-and-white framework with unverified arguments removed.
        """
        bw_framework = copy.deepcopy(self.culture.raw_bw_framework)

        # Delete defender's motion since challenger always proposes motion.
        bw_framework.remove_argument(0)
        # Delete motion verifiers.
        bw_framework.remove_argument(2)
        bw_framework.remove_argument(3)

        bw_framework.rank_least_attacked_arguments()

        # bw_framework.compute_rank_arguments_occurrence()

        # black_unverified = []
        # white_unverified = []
        # for argument_obj in self.culture.argumentation_framework.arguments():
        #     if not argument_obj.verify(defender, challenger):
        #         # Unverified by black.
        #         black_unverified.append(argument_obj.id())
        #     if not argument_obj.verify(challenger, defender):
        #         # Unverified by white.
        #         white_unverified.append(argument_obj.id())
        #
        # for argument_id in black_unverified:
        #     black_id = argument_id * 4
        #     bw_framework.remove_argument(black_id)
        #
        # for argument_id in white_unverified:
        #     white_id = argument_id * 4 + 1
        #     bw_framework.remove_argument(white_id)

        return bw_framework


    def interact_pair(self, defender: Agent, challenger: Agent):
        """
        Forces two agents to play the dialogue game.
        :param defender: Agent that currently is in front on the queue.
        :param challenger: Agent that is behind and wants to challenge the first.
        :return: True if status quo maintained or agents already interacted. False otherwise.
        """

        if defender.has_argued_with(challenger):
            return True

        logging.debug("#####################")
        logging.debug("Agent {} (defender) vs Agent {} (challenger)".format(defender.id, challenger.id))

        # Black = defender. White = challenger.
        # bw_framework = self.create_bw_framework(defender, challenger)

        defender.argued_with.append(challenger)
        challenger.argued_with.append(defender)

        defender.reset_privacy_budget()
        challenger.reset_privacy_budget()

        # Game starts with challenger agent proposing argument 1 ("We should swap places").
        used_arguments   = {defender: [], challenger: [1]}
        last_argument = {defender: [], challenger: [1]}
        privacy_budget  = {defender: defender.privacy_budget, challenger: challenger.privacy_budget}

        logging.debug("Agent {} uses argument 0".format(challenger.id))

        # Odd turns: defender. Even turns: challenger.
        turn = 1

        game_over = False
        winner = None
        while not game_over:
            if turn % 2:
                # Defender's turn.
                player   = defender
                opponent = challenger
            else:
                # Challenger's turn.
                player   = challenger
                opponent = defender
            logging.debug("TURN {}: Agent {}'s turn".format(turn, player.id))
            logging.debug(
                "Privacy budgets: Agent {}: {}  | Agent {}: {}".format(defender.id, privacy_budget[defender],
                                                                       challenger.id, privacy_budget[challenger]))

            # Remove previously used arguments.
            all_used_arguments = used_arguments[player] + used_arguments[opponent]
            forbidden_arguments = set(all_used_arguments)
            # Cannot pick argument that is attacked by previously used argument.
            forbidden_arguments.update(self.bw_framework.arguments_attacked_by_list(all_used_arguments))
            unverified_argument_ids = self.bw_framework.arguments_that_attack(last_argument[opponent])
            unverified_argument_ids = unverified_argument_ids.difference(forbidden_arguments)
            if self.strategy != ArgStrategy.ALL_ARGS:
                logging.debug("Possible attackers to argument {}: {}".format(last_argument[opponent], unverified_argument_ids))
            verified_argument_ids   = []
            for argument_id in unverified_argument_ids:
                argument_obj = self.bw_framework.argument(argument_id)
                # We will verify each argument using their respective verifier function.
                if (player == defender and is_black_arg(argument_id)) or \
                        (player == challenger and is_white_arg(argument_id)):
                    if argument_obj.verify(player, opponent):
                        verified_argument_ids.append(argument_id)

            # No local unfairness here. Agent had no counter-argument, regardless of privacy budget.
            if not verified_argument_ids:
                game_over = True
                winner    = opponent
                logging.debug("Agent {} cannot verify any argument!".format(player.id))
                logging.debug("Agent {} wins!".format(winner.id))
                logging.debug("Used arguments: {}".format(used_arguments[winner]))
                break

            logging.debug("Agent {} verified arguments {}".format(player.id, verified_argument_ids))

            affordable_argument_ids = []
            affordable_str = "Affordable arguments cost: "
            for argument_id in verified_argument_ids:
                argument_obj = self.bw_framework.argument(argument_id)
                if argument_obj.privacy_cost <= privacy_budget[player]:
                    player_is_defender = (player == defender)
                    if player_is_defender and is_black_arg(argument_id): # Black agent. Only even arguments are considered.
                        affordable_argument_ids.append(argument_id)
                    elif (not player_is_defender) and is_white_arg(argument_id): # White agent. Only odd arguments are considered.
                        affordable_argument_ids.append(argument_id)
                    affordable_str += "arg {}: {} | ".format(argument_id, argument_obj.privacy_cost)
            logging.debug(affordable_str)

            # If there are no affordable arguments, player loses and local unfairness increases.

            if self.strategy == ArgStrategy.RANDOM_CHOICE_PRIVATE:
                if not affordable_argument_ids:
                    game_over = True
                    winner = opponent
                    player.unfair_perception_score += 1
                    logging.debug("Agent {} cannot afford any argument!".format(player.id))
                    logging.debug("Agent {} wins!".format(winner.id))
                    logging.debug("Used arguments: {}".format(used_arguments[winner]))
                    break
                # Random choice within privacy budget.
                rebuttal_id = random.choice(affordable_argument_ids)
                logging.debug("Agent {} randomly chose argument {}".format(player.id, rebuttal_id))
                last_argument[player] = [rebuttal_id]
                used_arguments[player].append(rebuttal_id)
                rebuttal_obj = self.bw_framework.argument(rebuttal_id)
                privacy_budget[player] -= rebuttal_obj.privacy_cost

            elif self.strategy == ArgStrategy.RANDOM_CHOICE_NO_PRIVACY:
                # Random choice within verified arguments.
                rebuttal_id = random.choice(verified_argument_ids)
                logging.debug("Agent {} randomly chose argument {}".format(player.id, rebuttal_id))
                last_argument[player] = [rebuttal_id]
                used_arguments[player].append(rebuttal_id)

            elif self.strategy == ArgStrategy.GREEDY_MIN_PRIVACY:
                # FIXME: Remove duplication.
                if not affordable_argument_ids:
                    game_over = True
                    winner = opponent
                    player.unfair_perception_score += 1
                    logging.debug("Agent {} cannot afford any argument!".format(player.id))
                    logging.debug("Agent {} wins!".format(winner.id))
                    logging.debug("Used arguments: {}".format(used_arguments[winner]))
                    break
                # Deterministic choice with cheaper arguments first.
                cheaper_argument_obj = self.bw_framework.argument(affordable_argument_ids[0])
                for arg_id in affordable_argument_ids:
                    arg_obj = self.bw_framework.argument(arg_id)
                    if arg_obj.privacy_cost < cheaper_argument_obj.privacy_cost:
                        cheaper_argument_obj = arg_obj
                last_argument[player] = [cheaper_argument_obj.id()]
                logging.debug("Agent {} chose cheapest argument {}".format(player.id, last_argument[player]))
                used_arguments[player].append(cheaper_argument_obj.id())
                privacy_budget[player] -= cheaper_argument_obj.privacy_cost

            elif self.strategy == ArgStrategy.LEAST_ATTACKERS_PRIVATE:
                if not affordable_argument_ids:
                    game_over = True
                    winner = opponent
                    player.unfair_perception_score += 1
                    logging.debug("Agent {} cannot afford any argument!".format(player.id))
                    logging.debug("Agent {} wins!".format(winner.id))
                    logging.debug("Used arguments: {}".format(used_arguments[winner]))
                    break
                # argument_strength = self.bw_framework.argument_strength
                # min_strength = min(argument_strength.values())
                # max_strength = max(argument_strength.values())
                # if min_strength == max_strength:
                #     max_strength = 2
                #     min_strength = 1
                # strength_per_cost = {}
                # for arg_id, strength in argument_strength.items():
                #     privacy_cost = self.bw_framework.argument(arg_id).privacy_cost
                #     if privacy_cost == 0:
                #         privacy_cost = 1
                #     normalised_strength = ((strength - min_strength) / (max_strength - min_strength)) * 20
                #     strength_per_cost[arg_id] = normalised_strength / privacy_cost
                # argument_desc_rank = sorted(argument_strength, key=argument_strength.get, reverse=True)
                # relative_desc_rank = sorted(strength_per_cost, key=strength_per_cost.get, reverse=True)
                # if self.strategy == ArgStrategy.LEAST_ATTACKERS_PRIVATE:
                    # ranking = argument_desc_rank
                    # pass
                # else:
                #     ranking = relative_desc_rank

                ranking = self.bw_framework.least_attacked
                rebuttal_id = -1
                bw_argument_id = -1
                for bw_argument_id in ranking:
                    if bw_argument_id in affordable_argument_ids:
                        break
                # Convert bw id to normal id.
                rebuttal_id = bw_argument_id
                rebuttal_obj = self.bw_framework.argument(rebuttal_id)
                last_argument[player] = [rebuttal_id]
                logging.debug("Agent {} chose least attacked argument {}".format(player.id, last_argument[player]))
                used_arguments[player].append(rebuttal_id)
                privacy_budget[player] -= rebuttal_obj.privacy_cost

            elif self.strategy == ArgStrategy.LEAST_ATTACKERS_NO_PRIVACY:
                ranking = self.bw_framework.least_attacked
                bw_argument_id = -1
                for bw_argument_id in ranking:
                    if bw_argument_id in verified_argument_ids:
                        break
                rebuttal_id = bw_argument_id
                last_argument[player] = [rebuttal_id]
                logging.debug("Agent {} chose least attacked argument {}".format(player.id, last_argument[player]))
                used_arguments[player].append(rebuttal_id)

            elif self.strategy == ArgStrategy.ALL_ARGS:
                # Use all arguments as possible.
                attacked_arguments = set(self.bw_framework.arguments_attacked_by_list(verified_argument_ids))
                last_arguments = set(last_argument[opponent])
                if last_arguments.issubset(attacked_arguments):
                    logging.debug("Agent {} chose arguments {}".format(player.id, verified_argument_ids))
                    used_arguments[player].extend(verified_argument_ids)
                    last_argument[player] = verified_argument_ids
                else:
                    game_over = True
                    winner = opponent
                    logging.debug("Agent {} fails to attack all previous arguments!".format(player.id))
                    logging.debug("Agent {} wins!".format(winner.id))
                    logging.debug("Used arguments: {}".format(used_arguments[winner]))

            else:
                logging.error("AgentQueue::interact_pair: No valid strategy was chosen!")
                raise

            turn += 1

        return winner == defender

















