import subprocess
import string
import re
import random
import copy


from base_culture import Culture
from functools import partial
from argument import Argument, PrivateArgument, ArgumentationFramework


def always_true(*args, **kwargs):
    return True

class RandomCulture(Culture):
    num_properties = 100
    num_args = 40
    def __init__(self):
        # Properties of the culture with their default values go in self.properties.
        super().__init__()
        self.name = "Sample"
        self.properties = {}
        self.raw_bw_framework = None

        self.create_random_properties()
        self.create_arguments()
        self.define_attacks()
        self.generate_bw_framework()

    def create_random_properties(self):
        for i in range(0, self.num_properties):
            self.properties[i] = 0

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

        self.argumentation_framework.add_arguments(args)

    def define_attacks(self):
        """
        Defines attack relationships present in the culture.
        :return: Attack relationships.
        """
        num_attacks = self.num_args * 5
        for i in range(num_attacks):
            a = b = 0
            while a == b:  # Avoid self-attacks.
                a = random.randint(1, self.num_args-1)
                b = random.randint(0, self.num_args-1)
                # Avoid double arrows.
                if b in self.argumentation_framework.arguments_that_attack(a):
                    a = b = 0
                    continue

            self.argumentation_framework.add_attack(a, b)

    def generate_bw_framework(self):
        """
        This function generates and populates a black-and-white framework (forced bipartition) from an existing culture.
        A black-and-white framework is built with the following rules:
        1. Every argument is represented by 4 nodes, black and white X hypothesis and verified.
        2. Every attack between arguments is reconstructed between nodes of different colours.
        :return: A flat black-and-white framework.
        """
        self.raw_bw_framework = ArgumentationFramework()
        for argument in self.argumentation_framework.arguments():
            # Even indices for defender, odd for challenger.
            # Adding hypothetical arguments.
            black_hypothesis = PrivateArgument(arg_id = argument.id() * 4,
                                               descriptive_text = "b" + str(argument.id()),
                                               privacy_cost = argument.privacy_cost)
            black_hypothesis.set_verifier(always_true)
            white_hypothesis = PrivateArgument(arg_id = argument.id() * 4 + 1,
                                               descriptive_text = "w" + str(argument.id()),
                                               privacy_cost = argument.privacy_cost)
            white_hypothesis.set_verifier(always_true)

            # Adding verified arguments.
            black_verified = PrivateArgument(arg_id=argument.id() * 4 + 2,
                                             descriptive_text="V-b" + str(argument.id()),
                                             privacy_cost=argument.privacy_cost)
            black_verified.set_verifier(argument.verifier())

            white_verified = PrivateArgument(arg_id=argument.id() * 4 + 3,
                                             descriptive_text="V-w" + str(argument.id()),
                                             privacy_cost=argument.privacy_cost)
            white_verified.set_verifier(argument.verifier())

            self.raw_bw_framework.add_arguments([black_hypothesis, white_hypothesis, black_verified, white_verified])


            # Adding mutual attacks between verified arguments.
            self.raw_bw_framework.add_attack(black_verified.id(), white_verified.id())
            self.raw_bw_framework.add_attack(white_verified.id(), black_verified.id())

            # Adding attacks between immediate verified and hypothetical arguments.
            self.raw_bw_framework.add_attack(black_verified.id(), white_hypothesis.id())
            self.raw_bw_framework.add_attack(white_verified.id(), black_hypothesis.id())

        # Adding attacks between different arguments in original framework.
        # Each hypothesis attacks both the attacked hypothesis and verified arguments.
        for attacker_id, attacked_set in self.argumentation_framework.attacks().items():
            black_hypothesis_attacker_id = attacker_id * 4
            white_hypothesis_attacker_id = attacker_id * 4 + 1

            # Reproducing previous attacks, crossing between black and white nodes.
            for attacked_id in attacked_set:
                black_hypothesis_attacked_id = attacked_id * 4
                white_hypothesis_attacked_id = attacked_id * 4 + 1
                black_verified_attacked_id = attacked_id * 4 + 2
                white_verified_attacked_id = attacked_id * 4 + 3
                self.raw_bw_framework.add_attack(black_hypothesis_attacker_id, white_hypothesis_attacked_id)
                self.raw_bw_framework.add_attack(black_hypothesis_attacker_id, white_verified_attacked_id)
                self.raw_bw_framework.add_attack(white_hypothesis_attacker_id, black_hypothesis_attacked_id)
                self.raw_bw_framework.add_attack(white_hypothesis_attacker_id, black_verified_attacked_id)



# culture = RandomCulture()
# with open('sample.af',  'w') as file:
    # file.write(culture.argumentation_framework.to_aspartix())


# subprocess.run(["conarg_x64/conarg2", "-w dung", "-e admissible", "-c 4", "sample.af"])
# result = subprocess.run(["conarg_x64/conarg2", "-w dung", "-e conflictfree", "sample.af"],
#                          capture_output=True, text=True)
# result_string = result.stdout
# print(result_string)
# p = re.compile(r'\"[ *\d+]*\S\"')
# match = re.findall(r'\"[ *\d+]*\S\"', result_string)
# num_args = 10
# occurrences = {}
# for i in range(0, num_args):
#     occurrences[i] = 0
# for m in match:
#     m = m.replace("\"", "")
#     for i in range(0, num_args):
#         if str(i) in m:
#             occurrences[i] += 1
# print(occurrences)







