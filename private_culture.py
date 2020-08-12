import subprocess
import string
import re
import random


from base_culture import Culture
from functools import partial
from argument import Argument, PrivateArgument, ArgumentationFramework


class RandomCulture(Culture):
    num_properties = 100
    num_args = 7
    def __init__(self):
        # Properties of the culture with their default values go in self.properties.
        super().__init__()
        self.name = "Sample"
        self.properties = {}

        self.create_random_properties()
        self.create_arguments()
        self.define_attacks()

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
                                 descriptive_text = "We should swap places",
                                 privacy_cost = 0)
        motion.set_verifier(lambda gen: True)  # Propositional arguments are always valid.
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
        num_attacks = 12
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







