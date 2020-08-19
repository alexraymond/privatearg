import random
import copy
import scipy.stats as stats
import logging, sys
from enum import Enum
from private_culture import RandomCulture

class Agent:
    max_privacy_budget = 20
    def __init__(self, id):
        self.id = id
        self.properties = {}
        self.culture = None
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
                self.properties[key] = random.randint(0, 1000)

    def has_argued_with(self, agent_id):
        return agent_id in self.argued_with

class ArgumentationStrategy(Enum):
    RANDOM_CHOICE_NO_PRIVACY = 1
    RANDOM_CHOICE_WITH_PRIVACY = 2
    GREEDY_MIN_PRIVACY = 3
    COUNT_OCCURRENCES_ADMISSIBLE = 4
    ALL_ARGS = 5

class AgentQueue:

    def __init__(self, strategy: ArgumentationStrategy, size = 30):
        self.queue = []
        self.size = size
        self.culture = RandomCulture()
        self.init_queue()
        self.strategy = strategy

    def set_strategy(self, strategy):
        self.strategy = strategy

    def init_queue(self):
        for i in range(self.size):
            new_agent = Agent(i)
            new_agent.set_culture(self.culture)
            self.queue.append(new_agent)

    def queue_string(self):
        text = ""
        for agent in self.queue:
            text += str(agent.id) + " "
        return text

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
            i += 1
            ground_truth_ids.append(i)
        text = ""
        for agent in self.queue:
            text += str(base_dict[agent.id]) + " "
            relative_ids.append(base_dict[agent.id])
        tau, p = stats.kendalltau(ground_truth_ids, relative_ids)
        return text, tau, p

    def interact_all(self):
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
        while not stable_queue:
            stable_queue = True

            for scan in range(2):
                for i in range(1, self.size, 2):
                    i += scan
                    if i >= len(self.queue):
                        break
                    status_quo = self.interact_pair(self.queue[i-1], self.queue[i])
                    if not status_quo:
                        # Then swap.
                        self.queue[i-1], self.queue[i] = self.queue[i], self.queue[i-1]
                        stable_queue = False
                    logging.debug(self.queue_string())


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

        # Defender = black. Challenger = white.
        # bw_framework = copy.deepcopy(self.culture.bw_framework)

        defender.argued_with.append(challenger)
        challenger.argued_with.append(defender)

        defender.reset_privacy_budget()
        challenger.reset_privacy_budget()

        # Game starts with challenger agent proposing argument 0 ("We should swap places").
        used_arguments   = {defender: [], challenger: [0]}
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

            unverified_argument_ids = player.culture.arguments_that_attack_list(used_arguments[opponent])
            # Remove previously used arguments.
            all_used_arguments = used_arguments[player] + used_arguments[opponent]
            forbidden_arguments = set(all_used_arguments)
            # Cannot pick argument that is attacked by previously used argument.
            forbidden_arguments.update(player.culture.arguments_attacked_by_list(used_arguments[opponent]))
            unverified_argument_ids = unverified_argument_ids.difference(forbidden_arguments)
            logging.debug("Possible attackers to arguments {}: {}".format(used_arguments[opponent], unverified_argument_ids))
            verified_argument_ids   = []
            for argument_id in unverified_argument_ids:
                argument_obj = self.culture.argumentation_framework.argument(argument_id)
                # We will verify each argument using their respective verifier function.

                if argument_obj.verify(player, opponent):
                    verified_argument_ids.append(argument_id)

            # No local unfairness here. Agent had no counter-argument, regardless of privacy budget.
            if not verified_argument_ids:
                game_over = True
                winner    = opponent
                logging.debug("Agent {} wins!".format(winner.id))
                logging.debug("Used arguments: {}".format(used_arguments[winner]))
                break

            logging.debug("Agent {} verified arguments {}".format(player.id, verified_argument_ids))

            affordable_argument_ids = []
            for argument_id in verified_argument_ids:
                argument_obj = self.culture.argumentation_framework.argument(argument_id)
                if argument_obj.privacy_cost < privacy_budget[player]:
                    affordable_argument_ids.append(argument_id)

            # If there are no affordable arguments, player loses and local unfairness increases.

            if self.strategy == ArgumentationStrategy.RANDOM_CHOICE_WITH_PRIVACY:
                if not affordable_argument_ids:
                    game_over = True
                    winner = opponent
                    player.unfair_perception_score += 1
                    break
                # Random choice within privacy budget.
                rebuttal_id = random.choice(affordable_argument_ids)
                logging.debug("Agent {} chose argument {}".format(player.id, rebuttal_id))
                used_arguments[player].append(rebuttal_id)
                rebuttal_obj = self.culture.argumentation_framework.argument(rebuttal_id)
                privacy_budget[player] -= rebuttal_obj.privacy_cost

            elif self.strategy == ArgumentationStrategy.RANDOM_CHOICE_NO_PRIVACY:
                # Random choice within verified arguments.
                rebuttal_id = random.choice(verified_argument_ids)
                logging.debug("Agent {} chose argument {}".format(player.id, rebuttal_id))
                used_arguments[player].append(rebuttal_id)

            elif self.strategy == ArgumentationStrategy.GREEDY_MIN_PRIVACY:
                # FIXME: Remove duplication.
                if not affordable_argument_ids:
                    game_over = True
                    winner = opponent
                    player.unfair_perception_score += 1
                    break
                # Deterministic choice with cheaper arguments first.
                cheaper_argument_obj = self.culture.argumentation_framework.argument(affordable_argument_ids[0])
                for arg_id in affordable_argument_ids:
                    arg_obj = self.culture.argumentation_framework.argument(arg_id)
                    if arg_obj.privacy_cost < cheaper_argument_obj.privacy_cost:
                        cheaper_argument_obj = arg_obj
                used_arguments[player].append(cheaper_argument_obj.id)
                privacy_budget[player] -= cheaper_argument_obj.privacy_cost

            elif self.strategy == ArgumentationStrategy.COUNT_OCCURRENCES_ADMISSIBLE:


            elif self.strategy == ArgumentationStrategy.ALL_ARGS:
                # Use all arguments as possible.
                # FIXME: Not looking into budget for now.
                logging.debug("Agent {} chose arguments {}".format(player.id, verified_argument_ids))
                used_arguments[player].extend(verified_argument_ids)

            else:
                logging.error("AgentQueue::interact_pair: No valid strategy was chosen!")
                raise

            turn += 1

        return winner == defender

base_queue = AgentQueue(ArgumentationStrategy.RANDOM_CHOICE_WITH_PRIVACY)
base_str = base_queue.culture.argumentation_framework.to_aspartix()
bw_str = base_queue.culture.bw_framework.to_aspartix()
logging.debug(base_str)
# print(bw_str)



logging.debug("\n\n ATTEMPT 1 \n\n")
q1 = copy.deepcopy(base_queue)
q1.set_strategy(ArgumentationStrategy.ALL_ARGS)
q1.interact_all()
logging.debug("\n\n ATTEMPT 2 \n\n")
q2 = copy.deepcopy(base_queue)
q2.interact_all()
logging.debug("\n\n ATTEMPT 3 \n\n")
q3 = copy.deepcopy(base_queue)
q3.interact_all()
logging.debug("\n\n ATTEMPT 4 \n\n")
q4 = copy.deepcopy(base_queue)
q4.interact_all()
logging.debug("\n\n ATTEMPT 5 \n\n")
q5 = copy.deepcopy(base_queue)
q5.set_strategy(ArgumentationStrategy.RANDOM_CHOICE_NO_PRIVACY)
q5.interact_all()
logging.debug("\n\n ATTEMPT 6 \n\n")
q6 = copy.deepcopy(base_queue)
q6.set_strategy(ArgumentationStrategy.RANDOM_CHOICE_NO_PRIVACY)
q6.interact_all()
logging.debug("\n\n ATTEMPT 7 \n\n")
q7 = copy.deepcopy(base_queue)
q7.set_strategy(ArgumentationStrategy.RANDOM_CHOICE_NO_PRIVACY)
q7.interact_all()
logging.debug("\n\n ATTEMPT 8 \n\n")
q8 = copy.deepcopy(base_queue)
q8.set_strategy(ArgumentationStrategy.GREEDY_MIN_PRIVACY)
q8.interact_all()
logging.debug("\n\n ATTEMPT 9 \n\n")
q9 = copy.deepcopy(base_queue)
q9.set_strategy(ArgumentationStrategy.GREEDY_MIN_PRIVACY)
q9.interact_all()

print("GT: {}".format(q1.relative_queue(ground_truth=q1)))
print("P1: {}".format(q2.relative_queue(ground_truth=q1)))
print("P2: {}".format(q3.relative_queue(ground_truth=q1)))
print("P3: {}".format(q4.relative_queue(ground_truth=q1)))
print("R1: {}".format(q5.relative_queue(ground_truth=q1)))
print("R2: {}".format(q6.relative_queue(ground_truth=q1)))
print("R3: {}".format(q7.relative_queue(ground_truth=q1)))
print("GREEDY: {}".format(q8.relative_queue(ground_truth=q1)))

# q1_str = q1.culture.argumentation_framework.to_aspartix()
# q2_str = q2.culture.argumentation_framework.to_aspartix()
# q3_str = q3.culture.argumentation_framework.to_aspartix()
# q4_str = q4.culture.argumentation_framework.to_aspartix()
#
# all_strings = [base_str, q1_str, q2_str, q3_str, q4_str]
#
# for i in range(5):
#     for j in range(5):
#         if all_strings[i] != all_strings[j]:
#             print("Frameworks {} and {} are different!".format(i, j))
#         else:
#             print("Frameworks {} and {} are the same.".format(i, j))
# queue = AgentQueue(ArgumentationStrategy.RANDOM_CHOICE)
# queue2 = copy.deepcopy(queue)
# print("Order before interactions: {}".format(queue.queue_string()))
# queue.interact_all()
# print("Order after interactions: {}".format(queue.queue_string()))
#
# print("Order copy queue: {}".format(queue2.queue_string()))
# queue2.interact_all()
# print("Order copy queue after interactions: {}".format(queue2.queue_string()))
















