import subprocess
import string
import re
import random
import copy
import logging, sys
import os
import numpy as np

from base_culture import Culture
from functools import partial
from argument import Argument, PrivateArgument, ArgumentationFramework


# FIXME: Remove temporary debug stuff.
DEBUG_FILE = False
if DEBUG_FILE:
    LOG_FILENAME = 'debug2.log'
    if os.path.exists(LOG_FILENAME):
        os.remove(LOG_FILENAME)
    logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

def always_true(*args, **kwargs):
    # To be used as a function pointer.
    return True

class RandomCulture(Culture):
    """
    A random instantiation of a Culture, using random properties and rules.
    Each agent has a number of different properties with random values.
    The create_arguments and define_attacks functions define the structure of the argumentation framework.
    All verifier functions consist of simply checking the direction of inequality.
    """
    num_args = 50
    num_properties = num_args
    def __init__(self):
        # Properties of the culture with their default values go in self.properties.
        super().__init__()
        self.name = "Sample"
        self.properties = {}
        self.raw_alteroceptive_framework = None

        self.create_random_properties()
        # if DEBUG_FILE:
        #     self.load_framework()
        # else:
        self.create_arguments()
        # Commented out as we are assuming the property of transitivity.
        # self.define_attacks()
        self.define_attacks_transitive()
        self.generate_alteroceptive_framework()

    def create_random_properties(self):
        """
        Assigns random values to the culture properties.
        """
        for i in range(0, self.num_properties):
            self.properties[i] = random.randint(0, 1000)

    def load_framework(self):
        def generate_verifier_function(idx):
            """
            This helper function generates a unique verifier function for the culture arguments.
            :param idx: The argument ID.
            :return: A partial function object containing a callable verifier function prototype.
            """
            def verifier_prototype(idx, self_agent, other_agent):
                return self_agent.properties[idx] > other_agent.properties[idx]

            return partial(verifier_prototype, idx)

        random_costs = []
        for i in range(1, 20):
            random_costs.append(random.randint(1, 20))

        # Loading argumentation framework from aspartix file.
        with open('sample2.apx', 'r') as file:
            lines = file.readlines()
            for line in lines:
                if "arg" in line:
                    arg_id = int(line[line.find("(")+1 : line.find(")")])
                    new_arg = PrivateArgument(arg_id= arg_id,
                                              descriptive_text=str(arg_id),
                                              privacy_cost= 0 if arg_id == 0 else random_costs[int(arg_id/4)])
                    if arg_id == 0:
                        new_arg.set_verifier(always_true)
                    else:
                        new_arg.set_verifier(generate_verifier_function(idx=new_arg.id()))
                    self.AF.add_argument(new_arg)
                if "att" in line:
                    attack = line[line.find("(")+1 : line.find(")")]
                    pair = attack.split(",")
                    attacker = int(pair[0])
                    attacked = int(pair[1])
                    self.AF.add_attack(attacker, attacked)
        # self.argumentation_framework.stats()


    def create_arguments(self):
        """
        Defines set of arguments present in the culture.
        :return: Set of arguments.
        """
        args = []

        motion = PrivateArgument(arg_id = 0,
                                 descriptive_text = "M",
                                 privacy_cost = 0)

        motion.set_verifier(always_true)  # Propositional arguments are always valid.
        args.append(motion)

        def generate_verifier_function(idx):
            """
            This helper function generates a unique verifier function for the culture arguments.
            :param idx: The argument ID.
            :return: A partial function object containing a callable verifier function prototype.
            """
            def verifier_prototype(idx, self_agent, other_agent):
                return self_agent.properties[idx] > other_agent.properties[idx]

            # idx = random.randrange(1, self.num_properties)
            return partial(verifier_prototype, idx)

        for i in range(1, self.num_args):
            # Generating random arguments to test solver.
            new_arg = PrivateArgument(arg_id = i,
                                      descriptive_text = str(i),
                                      privacy_cost = random.randint(1, 20))
            # Randomly generated verifier function.
            new_arg.set_verifier(generate_verifier_function(idx=new_arg.id()))
            args.append(new_arg)

        self.AF.add_arguments(args)

    def define_attacks(self):
        """
        Defines attack relationships present in the culture.
        :return: Attack relationships.
        """
        num_attacks = self.num_args * 8
        connected = set()
        connected.add(0)
        # num_attacks = 12
        for i in range(num_attacks):
            a = b = 0
            while a == b:  # Avoid self-attacks.
                a = random.randint(1, self.num_args-1)
                b = random.choice(list(connected))
                # Avoid double arrows.
                if b in self.AF.arguments_that_attack(a) or b > a:
                    a = b = 0
                    continue

            self.AF.add_attack(a, b)
            connected.add(a)
            connected.add(b)

        for arg_id in self.AF.all_arguments.copy().keys():
            if arg_id not in connected:
                self.AF.remove_argument(arg_id)
        # self.argumentation_framework.make_spanning_graph()

        leaves = set()
        for id in self.AF.argument_ids():
            if id not in self.AF.attacked_by().keys():
                leaves.add(id)
        # print("Number of maximal arguments before: {}".format(len(leaves)))

        # self.argumentation_framework.stats()

    def define_attacks_transitive(self, ensure_single_winner=True):
        """
        Defines attack relationships present in the culture.
        :return: Attack relationships.
        """

        def replicate_attacks(a, to_visit, visited):
            """
            Performs a breadth-first search to make sure that attacks are replicated to
            ensure transitivity.
            :param a: Current argument.
            """
            while to_visit:
                current_arg = to_visit.pop()
                if current_arg in visited:
                    continue
                if current_arg in self.AF.arguments_that_attack(a):
                    continue
                if a > current_arg:
                    self.AF.add_attack(a, current_arg)
                to_visit.update(self.AF.arguments_attacked_by(current_arg))
                visited.add(current_arg)

        # Use a stochastic approach to building the graph.
        num_attacks = self.num_args * 8
        connected = set()
        connected.add(0)
        for i in range(num_attacks):
            a = b = 0
            while a == b:  # Avoid self-attacks.
                a = random.randint(1, self.num_args-1)
                b = random.choice(list(connected))
                # Avoid double arrows.
                if b in self.AF.arguments_that_attack(a) or b > a:
                    a = b = 0
                    continue
            self.AF.add_attack(a, b)
            connected.add(a)
            connected.add(b)

            # Replicate attacks recursively
            to_visit = self.AF.arguments_attacked_by(b).copy()
            visited = set()

            replicate_attacks(a, to_visit, visited)

        for arg_id in self.AF.all_arguments.copy().keys():
            if arg_id not in connected:
                self.AF.remove_argument(arg_id)

        leaves = set()
        for id in self.AF.argument_ids():
            if id not in self.AF.attacked_by().keys():
                leaves.add(id)
        print("Number of maximal arguments before: {}".format(len(leaves)))

    def generate_alteroceptive_framework(self):
        """
        This function generates and populates an alteroceptive framework (forced bipartition) from an existing culture.
        An alteroceptive framework is built with the following rules:
        1. Every argument is represented by 4 nodes, black and white X hypothesis and verified.
        2. Every attack between arguments is reconstructed between nodes of different colours.
        :return: A flat black-and-white framework.
        """
        self.raw_alteroceptive_framework = ArgumentationFramework()
        for argument in self.AF.arguments():
            # Even indices for defender, odd for challenger.
            # Adding hypothetical arguments.
            black_hypothesis = PrivateArgument(arg_id = argument.id() * 4,
                                               descriptive_text = argument.hypothesis_text,
                                               privacy_cost = argument.privacy_cost)
            white_hypothesis = PrivateArgument(arg_id = argument.id() * 4 + 1,
                                               descriptive_text = argument.hypothesis_text,
                                               privacy_cost = argument.privacy_cost)
            h_verifier = argument.hypothesis_verifier if argument.hypothesis_verifier else always_true
            black_hypothesis.set_verifier(h_verifier)
            white_hypothesis.set_verifier(h_verifier)

            # Adding verified arguments.
            black_verified = PrivateArgument(arg_id=argument.id() * 4 + 2,
                                             descriptive_text=argument.verified_fact_text,
                                             privacy_cost=argument.privacy_cost)
            white_verified = PrivateArgument(arg_id=argument.id() * 4 + 3,
                                             descriptive_text=argument.verified_fact_text,
                                             privacy_cost=argument.privacy_cost)
            f_verifier = argument.fact_verifier if argument.fact_verifier else argument.verifier()
            black_verified.set_verifier(f_verifier)
            white_verified.set_verifier(f_verifier)

            self.raw_alteroceptive_framework.add_arguments([black_hypothesis, white_hypothesis, black_verified, white_verified])

            # Adding mutual attacks between contradictory hypotheses.
            self.raw_alteroceptive_framework.add_attack(black_hypothesis.id(), white_hypothesis.id())
            self.raw_alteroceptive_framework.add_attack(white_hypothesis.id(), black_hypothesis.id())

            # Adding mutual attacks between contradictory verified arguments.
            self.raw_alteroceptive_framework.add_attack(black_verified.id(), white_verified.id())
            self.raw_alteroceptive_framework.add_attack(white_verified.id(), black_verified.id())

            # Adding attacks between immediate verified and hypothetical arguments.
            self.raw_alteroceptive_framework.add_attack(black_verified.id(), white_hypothesis.id())
            self.raw_alteroceptive_framework.add_attack(white_verified.id(), black_hypothesis.id())

        # Adding attacks between different arguments in original framework.
        # Each hypothesis attacks both the attacked hypothesis and verified arguments.
        for attacker_id, attacked_set in self.AF.attacks().items():
            black_hypothesis_attacker_id = attacker_id * 4
            white_hypothesis_attacker_id = attacker_id * 4 + 1

            # Reproducing previous attacks, crossing between black and white nodes.
            for attacked_id in attacked_set:
                black_hypothesis_attacked_id = attacked_id * 4
                white_hypothesis_attacked_id = attacked_id * 4 + 1
                black_verified_attacked_id = attacked_id * 4 + 2
                white_verified_attacked_id = attacked_id * 4 + 3
                self.raw_alteroceptive_framework.add_attack(black_hypothesis_attacker_id, white_hypothesis_attacked_id)
                self.raw_alteroceptive_framework.add_attack(black_hypothesis_attacker_id, white_verified_attacked_id)
                self.raw_alteroceptive_framework.add_attack(white_hypothesis_attacker_id, black_hypothesis_attacked_id)
                self.raw_alteroceptive_framework.add_attack(white_hypothesis_attacker_id, black_verified_attacked_id)









