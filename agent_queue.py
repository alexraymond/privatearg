import subprocess
import string
import re
import random
import copy
import scipy.stats as stats
import logging, sys
import numpy as np
import os
import subprocess
import json
from multiprocessing.pool import ThreadPool

from utils import *
from enum import Enum, IntEnum
from private_culture import RandomCulture
from boat_culture import BoatCulture
from agent import Agent
from boat_agent import BoatAgent


class ArgStrategy(Enum):
    RANDOM_CHOICE_NO_PRIVACY = 1
    RANDOM_CHOICE_PRIVATE = 2
    LEAST_COST_PRIVATE = 3
    LEAST_ATTACKERS_PRIVATE = 4
    LEAST_ATTACKERS_NO_PRIVACY = 5
    COUNT_OCCURRENCES_ADMISSIBLE_RELATIVE = 6
    ALL_ARGS = 7
    MOST_ATTACKS_PRIVATE = 8
    MOST_ATTACKS_NO_PRIVACY = 9
    LEAST_COST_NO_PRIVACY = 10


class AgentQueue:
    """
    Contains a collection of agents in a queue, where they will perform pairwise interactions.
    """
    TOTAL_YES = 0
    TOTAL_NO = 0
    TOTAL_BAD = 0

    def __init__(self, strategy: ArgStrategy, culture=None, size=30, privacy_budget=10):
        """
        Initialises the queue.
        :param strategy: The strategy used by all agents.
        :param culture: The culture shared by all agents.
        :param size: The size of the queue.
        :param privacy_budget: Privacy budget of all agents.
        """
        self.queue = []
        self.size = size
        self.culture = RandomCulture() if culture is None else copy.deepcopy(culture)
        self.init_queue(privacy_budget)
        self.strategy = strategy
        self.alteroceptive_framework = None
        self.rate_local_unfairness = 0
        self.string = ""

    def set_privacy_budget(self, privacy_budget):
        for agent in self.queue:
            agent.set_max_privacy_budget(privacy_budget)

    def set_strategy(self, strategy):
        self.strategy = strategy

    def init_queue(self, privacy_budget):
        for i in range(self.size):
            if type(self.culture) is BoatCulture:
                new_boat = BoatAgent(i, max_privacy_budget=privacy_budget)
                new_boat.set_culture(self.culture)
                self.culture.initialise_random_agent(new_boat)
                self.queue.append(new_boat)
            else:
                new_agent = Agent(i, max_privacy_budget=privacy_budget)
                new_agent.set_culture(self.culture)
                self.queue.append(new_agent)

    def results_to_dict(self):
        data = {}
        data["size"] = self.size
        data["strategy"] = str(self.strategy)
        data["agents"] = {}
        for agent in self.queue:
            data["agents"][agent.id] = agent.results_to_dict()
        return data

    def agents_to_dict(self):
        data = {}
        for agent in self.queue:
            data[agent.id] = agent.properties_to_dict()
        return data

    def queue_string(self):
        text = ""
        for agent in self.queue:
            text += str(agent.id) + " "
        return text

    def compute_ground_truth(self, debug=False):
        """
        Computes the ground truth by removing all unverified arguments from BW framework
        and calculating skeptical acceptance of motion.
        :return: Sorted ground truth.
        """
        ground_truth = copy.deepcopy(self)
        ground_truth.alteroceptive_framework = ground_truth.create_alteroceptive_framework()
        if debug:
            print("BASE BW FRAMEWORK:\n{}".format(ground_truth.alteroceptive_framework))
        status_quo = {}
        for i in range(0, len(ground_truth.queue)):
            for j in range(0, len(ground_truth.queue)):
                if i == j:
                    continue
                defender = ground_truth.queue[i]
                challenger = ground_truth.queue[j]
                alteroceptive_framework = copy.deepcopy(ground_truth.alteroceptive_framework)

                to_remove = []
                for argument_id in alteroceptive_framework.all_arguments:
                    argument_obj = alteroceptive_framework.argument(argument_id)
                    if is_black_arg(argument_id):
                        verified = argument_obj.verify(defender, challenger)
                    else:
                        verified = argument_obj.verify(challenger, defender)
                    if not verified:
                        to_remove.append(argument_id)


                for argument_id in to_remove:
                    alteroceptive_framework.remove_argument(argument_id)

                solver_result = alteroceptive_framework.run_solver(semantics="DS-PR", arg_str="1")
                pair = (defender.id, challenger.id)
                if "YES" in solver_result:
                    # Challenger wins.
                    attackers_of_1 = alteroceptive_framework.arguments_that_attack(1)

                    anti_pair = (challenger.id, defender.id)
                    self.TOTAL_YES += 1
                    logging.debug(
                        "DEFENDER {} vs CHALLENGER {}:\nWINNER: {}".format(defender.id, challenger.id, challenger.id))
                    status_quo[pair] = False
                elif "NO" in solver_result:
                    # Defender wins.
                    attackers_of_1 = alteroceptive_framework.arguments_that_attack(1)
                    # pair = (challenger.id, defender.id)
                    anti_pair = (defender.id, challenger.id)
                    self.TOTAL_NO += 1
                    logging.debug(
                        "DEFENDER {} vs CHALLENGER {}:\nWINNER: {}".format(defender.id, challenger.id, defender.id))
                    status_quo[pair] = True
                else:
                    print("Error computing extensions")

                # logging.debug("FRAMEWORK FOR PAIR B{} W{}:".format(defender.id, challenger.id))
                # logging.debug(alteroceptive_framework.to_aspartix_text())
                # status_quo[pair] = False
                # status_quo[anti_pair] = True

        # Get queue order.
        swaps = ground_truth.interact_all(gt_result=status_quo)
        print("Ground truth: {}".format(ground_truth.queue_string()))
        print("GT Swaps: {}".format(swaps))
        print("Total yes: {}\nTotal no: {}".format(self.TOTAL_YES, self.TOTAL_NO))
        return ground_truth, self.TOTAL_YES, swaps, status_quo

    def compute_ground_truth_matrix(self):
        """
        Computes the ground truth by removing all unverified arguments from BW framework
        and calculating skeptical acceptance of motion.
        :return: Sorted ground truth.
        """
        ground_truth = copy.deepcopy(self)
        ground_truth.alteroceptive_framework = ground_truth.create_alteroceptive_framework()
        winners = {}
        for i in range(0, len(ground_truth.queue)):
            for j in range(0, len(ground_truth.queue)):
                if i == j:
                    continue
                defender = ground_truth.queue[i]
                challenger = ground_truth.queue[j]
                alteroceptive_framework = copy.deepcopy(ground_truth.alteroceptive_framework)

                to_remove = []
                for argument_id in alteroceptive_framework.all_arguments:
                    argument_obj = alteroceptive_framework.argument(argument_id)
                    if is_black_arg(argument_id):
                        verified = argument_obj.verify(defender, challenger)
                    else:
                        verified = argument_obj.verify(challenger, defender)
                    if not verified:
                        to_remove.append(argument_id)
                        # if is_verified_arg(argument_id):
                        #     to_remove.append(argument_id - 2)

                for argument_id in to_remove:
                    alteroceptive_framework.remove_argument(argument_id)

                solver_result = alteroceptive_framework.run_solver(semantics="DS-PR", arg_str="1")
                if "YES" in solver_result:
                    # Challenger wins.
                    winners[(defender.id, challenger.id)] = challenger.id
                    self.TOTAL_YES += 1
                elif "NO" in solver_result:
                    # Defender wins.
                    winners[(defender.id, challenger.id)] = defender.id
                    self.TOTAL_NO += 1
                else:
                    print("Error computing extensions")

        return winners

    def compute_ground_truth_matrix_parallel(self):
        """
        Computes the ground truth by removing all unverified arguments from BW framework
        and calculating skeptical acceptance of motion.
        :return: Sorted ground truth.
        """
        ground_truth = copy.deepcopy(self)
        ground_truth.alteroceptive_framework = ground_truth.create_alteroceptive_framework()
        winners = {}
        pairs = []
        for i in range(0, len(ground_truth.queue)):
            for j in range(0, len(ground_truth.queue)):
                if i == j:
                    continue
                defender = ground_truth.queue[i]
                challenger = ground_truth.queue[j]
                alteroceptive_framework = copy.deepcopy(ground_truth.alteroceptive_framework)

                to_remove = []
                for argument_id in alteroceptive_framework.all_arguments:
                    argument_obj = alteroceptive_framework.argument(argument_id)
                    if is_black_arg(argument_id):
                        verified = argument_obj.verify(defender, challenger)
                    else:
                        verified = argument_obj.verify(challenger, defender)
                    if not verified:
                        to_remove.append(argument_id)
                        # if is_verified_arg(argument_id):
                        #     to_remove.append(argument_id - 2)

                for argument_id in to_remove:
                    alteroceptive_framework.remove_argument(argument_id)

                filename = "temp_frameworks/{}-{}.apx".format(defender.id, challenger.id)
                with open(filename, 'w') as file:
                    file.write(alteroceptive_framework.to_aspartix_id())
                pairs.append((defender.id, challenger.id))

        def run_solver_detached(pair):
            defender, challenger = pair
            filename = "temp_frameworks/{}-{}.apx".format(defender, challenger)
            solver_location = "mu-toksia/mu-toksia.exe"
            semantics = "DS-PR"
            arg_str = "1"
            result = subprocess.run([solver_location, "-p", semantics, "-fo", "apx", "-f", filename,
                                     "-a", arg_str],
                                    capture_output=True, text=True)
            return result.stdout

        thread_pool = ThreadPool()
        solver_results = thread_pool.map(run_solver_detached, pairs)
        thread_pool.close()
        thread_pool.join()
        results = list(zip(solver_results, pairs))

        for result in results:
            solver_result, (defender, challenger) = result
            if "YES" in solver_result:
                # Challenger wins.
                winners[(defender, challenger)] = challenger
                self.TOTAL_YES += 1
            elif "NO" in solver_result:
                # Defender wins.
                winners[(defender, challenger)] = defender
                self.TOTAL_NO += 1
            else:
                print("Error computing extensions")

        return winners

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
        return self.queue_string(), tau, p

    def interact_all_matrix(self):
        logging.debug(self.queue_string())
        self.alteroceptive_framework = self.create_alteroceptive_framework()
        interaction_count = 0
        winners = {}

        for i in range(0, self.size):
            for j in range(0, self.size):
                if i == j:
                    continue
                defender = self.queue[i]
                challenger = self.queue[j]
                # if defender.has_argued_with(challenger):
                #     return True

                status_quo, considered_unfair, privacy_cost = self.interact_pair(self.queue[i], self.queue[j])
                winner = defender.id if status_quo else challenger.id
                pair = (defender, challenger)
                defender.add_result(pair, privacy_cost, winner, considered_unfair)
                challenger.add_result(pair, privacy_cost, winner, considered_unfair)
                winners[(defender.id, challenger.id)] = winner
                interaction_count += 1

        aggregate_local_unfairness = 0
        for agent in self.queue:
            aggregate_local_unfairness += agent.unfair_perception_score
        self.rate_local_unfairness = aggregate_local_unfairness / interaction_count
        return winners

    def interact_all(self, gt_result=None):
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
        self.alteroceptive_framework = self.create_alteroceptive_framework()
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
                        status_quo = self.interact_pair(self.queue[i - 1], self.queue[i])
                    else:
                        status_quo = gt_result[self.queue[i - 1].id, self.queue[i].id]
                    interaction_count += 1
                    if not status_quo:
                        # Then swap.
                        self.queue[i - 1], self.queue[i] = self.queue[i], self.queue[i - 1]
                        swaps += 1
                        stable_queue = False
                    logging.debug(self.queue_string())
        aggregate_local_unfairness = 0
        for agent in self.queue:
            aggregate_local_unfairness += agent.unfair_perception_score
        self.rate_local_unfairness = aggregate_local_unfairness / interaction_count
        self.string = self.queue_string()
        return swaps

    def create_alteroceptive_framework(self):
        """
        Prunes unverified arguments out of a black-and-white framework.
        :param defender: Agent representing black arguments.
        :param challenger: Agent representing white arguments.
        :return: Black-and-white framework with unverified arguments removed.
        """
        alteroceptive_framework = copy.deepcopy(self.culture.raw_alteroceptive_framework)

        # Delete defender's motion since challenger always proposes motion.
        alteroceptive_framework.remove_argument(0)
        # Delete motion verifiers.
        alteroceptive_framework.remove_argument(2)
        alteroceptive_framework.remove_argument(3)

        alteroceptive_framework.rank_least_attacked_arguments()
        alteroceptive_framework.rank_strongest_attacker_arguments()

        return alteroceptive_framework

    def interact_pair(self, defender: Agent, challenger: Agent):
        """
        Forces two agents to play the dialogue game.
        :param defender: Agent that currently is in front on the queue.
        :param challenger: Agent that is behind and wants to challenge the first.
        :return: True if status quo maintained or agents already interacted. False otherwise.
        """

        # FIXME: Should this be removed?
        # if defender.has_argued_with(challenger):
        #     return True

        logging.debug("#####################")
        logging.debug("Agent {} (defender) vs Agent {} (challenger)".format(defender.id, challenger.id))
        logging.debug("PROPERTIES:\n")
        for property in self.culture.properties.keys():
            if type(property) == str:
                logging.debug("Property[{}]: {}  vs.  {}".format(str(property), getattr(defender, property),
                                                                 getattr(challenger, property)))
            else:
                logging.debug("Property[{}]: {}  vs.  {}".format(str(property), defender.properties[property],
                                                                 challenger.properties[property]))

        # Black = defender. White = challenger.
        # alteroceptive_framework = self.create_alteroceptive_framework(defender, challenger)

        defender.argued_with.append(challenger)
        challenger.argued_with.append(defender)

        defender.reset_privacy_budget()
        challenger.reset_privacy_budget()

        # Game starts with challenger agent proposing argument 1 ("We should swap places").
        used_arguments = {defender: [], challenger: [1]}
        last_argument = {defender: [], challenger: [1]}
        privacy_budget = {defender: defender.privacy_budget, challenger: challenger.privacy_budget}

        logging.debug("Agent {} uses argument 0".format(challenger.id))

        # Odd turns: defender. Even turns: challenger.
        turn = 1

        game_over = False
        winner = None
        considered_unfair = False
        while not game_over:
            if turn % 2:
                # Defender's turn.
                player = defender
                opponent = challenger
            else:
                # Challenger's turn.
                player = challenger
                opponent = defender
            logging.debug("TURN {}: Agent {}'s turn".format(turn, player.id))
            logging.debug(
                "Privacy budgets: Agent {}: {}  | Agent {}: {}".format(defender.id, privacy_budget[defender],
                                                                       challenger.id, privacy_budget[challenger]))

            # Remove previously used arguments.
            all_used_arguments = used_arguments[player] + used_arguments[opponent]
            forbidden_arguments = set(all_used_arguments)
            # Cannot pick argument that is attacked by previously used argument.
            forbidden_arguments.update(self.alteroceptive_framework.arguments_attacked_by_list(all_used_arguments))
            unverified_argument_ids = self.alteroceptive_framework.arguments_that_attack(last_argument[opponent])
            unverified_argument_ids = unverified_argument_ids.difference(forbidden_arguments)
            if self.strategy != ArgStrategy.ALL_ARGS:
                logging.debug(
                    "Possible attackers to argument {}: {}".format(last_argument[opponent], unverified_argument_ids))
            verified_argument_ids = []
            for argument_id in unverified_argument_ids:
                argument_obj = self.alteroceptive_framework.argument(argument_id)
                # We will verify each argument using their respective verifier function.
                if (player == defender and is_black_arg(argument_id)) or \
                        (player == challenger and is_white_arg(argument_id)):
                    if argument_obj.verify(player, opponent):
                        verified_argument_ids.append(argument_id)

            # No local unfairness here. Agent had no counter-argument, regardless of privacy budget.
            if not verified_argument_ids:
                game_over = True
                winner = opponent
                logging.debug("Agent {} cannot verify any argument!".format(player.id))
                logging.debug("Agent {} wins!".format(winner.id))
                logging.debug("Used arguments: {}".format(used_arguments[winner]))
                break

            logging.debug("Agent {} verified arguments {}".format(player.id, verified_argument_ids))

            affordable_argument_ids = []
            affordable_str = "Affordable arguments cost: "
            for argument_id in verified_argument_ids:
                argument_obj = self.alteroceptive_framework.argument(argument_id)
                if argument_obj.privacy_cost <= privacy_budget[player]:
                    player_is_defender = (player == defender)
                    if player_is_defender and is_black_arg(
                            argument_id):  # Black agent. Only even arguments are considered.
                        affordable_argument_ids.append(argument_id)
                    elif (not player_is_defender) and is_white_arg(
                            argument_id):  # White agent. Only odd arguments are considered.
                        affordable_argument_ids.append(argument_id)
                    affordable_str += "arg {}: {} | ".format(argument_id, argument_obj.privacy_cost)
            logging.debug(affordable_str)

            # If there are no affordable arguments, player loses and local unfairness increases.

            if self.strategy == ArgStrategy.RANDOM_CHOICE_PRIVATE:
                if not affordable_argument_ids:
                    game_over = True
                    winner = opponent
                    player.unfair_perception_score += 1
                    considered_unfair = True
                    logging.debug("Agent {} cannot afford any argument!".format(player.id))
                    logging.debug("Agent {} wins!".format(winner.id))
                    logging.debug("Used arguments: {}".format(used_arguments[winner]))
                    break
                # Random choice within privacy budget.
                rebuttal_id = random.choice(affordable_argument_ids)
                logging.debug("Agent {} randomly chose argument {}".format(player.id, rebuttal_id))
                last_argument[player] = [rebuttal_id]
                used_arguments[player].append(rebuttal_id)
                rebuttal_obj = self.alteroceptive_framework.argument(rebuttal_id)
                # print("Agent {}: {}".format(player.id, rebuttal_obj.descriptive_text))
                privacy_budget[player] -= rebuttal_obj.privacy_cost

            elif self.strategy == ArgStrategy.RANDOM_CHOICE_NO_PRIVACY:
                # Random choice within verified arguments.
                rebuttal_id = random.choice(verified_argument_ids)
                logging.debug("Agent {} randomly chose argument {}".format(player.id, rebuttal_id))
                last_argument[player] = [rebuttal_id]
                used_arguments[player].append(rebuttal_id)

            elif self.strategy == ArgStrategy.LEAST_COST_PRIVATE:
                # FIXME: Remove duplication.
                if not affordable_argument_ids:
                    game_over = True
                    winner = opponent
                    player.unfair_perception_score += 1
                    considered_unfair = True
                    logging.debug("Agent {} cannot afford any argument!".format(player.id))
                    logging.debug("Agent {} wins!".format(winner.id))
                    logging.debug("Used arguments: {}".format(used_arguments[winner]))
                    break
                # Deterministic choice with cheaper arguments first.
                cheaper_argument_obj = self.alteroceptive_framework.argument(affordable_argument_ids[0])
                for arg_id in affordable_argument_ids:
                    arg_obj = self.alteroceptive_framework.argument(arg_id)
                    if arg_obj.privacy_cost < cheaper_argument_obj.privacy_cost:
                        cheaper_argument_obj = arg_obj
                last_argument[player] = [cheaper_argument_obj.id()]
                logging.debug("Agent {} chose cheapest argument {}".format(player.id, last_argument[player]))
                used_arguments[player].append(cheaper_argument_obj.id())
                privacy_budget[player] -= cheaper_argument_obj.privacy_cost

            elif self.strategy == ArgStrategy.LEAST_COST_NO_PRIVACY:
                # Deterministic choice with cheaper arguments first.
                cheaper_argument_obj = self.alteroceptive_framework.argument(verified_argument_ids[0])
                for arg_id in verified_argument_ids:
                    arg_obj = self.alteroceptive_framework.argument(arg_id)
                    if arg_obj.privacy_cost < cheaper_argument_obj.privacy_cost:
                        cheaper_argument_obj = arg_obj
                last_argument[player] = [cheaper_argument_obj.id()]
                logging.debug("Agent {} chose cheapest argument {}".format(player.id, last_argument[player]))
                used_arguments[player].append(cheaper_argument_obj.id())

            elif self.strategy == ArgStrategy.LEAST_ATTACKERS_PRIVATE:
                if not affordable_argument_ids:
                    game_over = True
                    winner = opponent
                    player.unfair_perception_score += 1
                    considered_unfair = True
                    logging.debug("Agent {} cannot afford any argument!".format(player.id))
                    logging.debug("Agent {} wins!".format(winner.id))
                    logging.debug("Used arguments: {}".format(used_arguments[winner]))
                    break

                ranking = self.alteroceptive_framework.least_attacked
                rebuttal_id = -1
                alteroceptive_argument_id = -1
                for alteroceptive_argument_id in ranking:
                    if alteroceptive_argument_id in affordable_argument_ids:
                        break
                # Convert bw id to normal id.
                rebuttal_id = alteroceptive_argument_id
                rebuttal_obj = self.alteroceptive_framework.argument(rebuttal_id)
                last_argument[player] = [rebuttal_id]
                logging.debug("Agent {} chose least attacked argument {}".format(player.id, last_argument[player]))
                used_arguments[player].append(rebuttal_id)
                privacy_budget[player] -= rebuttal_obj.privacy_cost

            elif self.strategy == ArgStrategy.LEAST_ATTACKERS_NO_PRIVACY:
                ranking = self.alteroceptive_framework.least_attacked
                alteroceptive_argument_id = -1
                for alteroceptive_argument_id in ranking:
                    if alteroceptive_argument_id in verified_argument_ids:
                        break
                rebuttal_id = alteroceptive_argument_id
                last_argument[player] = [rebuttal_id]
                logging.debug("Agent {} chose least attacked argument {}".format(player.id, last_argument[player]))
                used_arguments[player].append(rebuttal_id)

            elif self.strategy == ArgStrategy.MOST_ATTACKS_PRIVATE:
                if not affordable_argument_ids:
                    game_over = True
                    winner = opponent
                    player.unfair_perception_score += 1
                    considered_unfair = True
                    logging.debug("Agent {} cannot afford any argument!".format(player.id))
                    logging.debug("Agent {} wins!".format(winner.id))
                    logging.debug("Used arguments: {}".format(used_arguments[winner]))
                    break

                ranking = self.alteroceptive_framework.strongest_attackers
                rebuttal_id = -1
                alteroceptive_argument_id = -1
                for alteroceptive_argument_id in ranking:
                    if alteroceptive_argument_id in affordable_argument_ids:
                        break
                # Convert bw id to normal id.
                rebuttal_id = alteroceptive_argument_id
                rebuttal_obj = self.alteroceptive_framework.argument(rebuttal_id)
                last_argument[player] = [rebuttal_id]
                logging.debug("Agent {} chose most attacking argument {}".format(player.id, last_argument[player]))
                used_arguments[player].append(rebuttal_id)
                privacy_budget[player] -= rebuttal_obj.privacy_cost

            elif self.strategy == ArgStrategy.MOST_ATTACKS_NO_PRIVACY:
                ranking = self.alteroceptive_framework.strongest_attackers
                alteroceptive_argument_id = -1
                for alteroceptive_argument_id in ranking:
                    if alteroceptive_argument_id in verified_argument_ids:
                        break
                rebuttal_id = alteroceptive_argument_id
                last_argument[player] = [rebuttal_id]
                logging.debug("Agent {} chose most attacking argument {}".format(player.id, last_argument[player]))
                used_arguments[player].append(rebuttal_id)

            elif self.strategy == ArgStrategy.ALL_ARGS:
                # Use all arguments as possible.
                attacked_arguments = set(self.alteroceptive_framework.arguments_attacked_by_list(verified_argument_ids))
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

        total_privacy_cost = (defender.max_privacy_budget - privacy_budget[defender]) +\
                             (challenger.max_privacy_budget - privacy_budget[challenger])
        return (winner == defender), considered_unfair, total_privacy_cost
