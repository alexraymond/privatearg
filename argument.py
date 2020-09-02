import subprocess
import string
import re

class Argument:
    def __init__(self, arg_id, descriptive_text):
        self.__arg_id = arg_id
        self.__descriptive_text = descriptive_text
        self.__framework = None
        self.evidence = []
        self.verifier_function = None

    def id(self):
        return self.__arg_id

    def set_framework(self, framework):
        self.__framework = framework

    def add_evidence(self, evidence):
        self.evidence.append(evidence)

    def descriptive_text(self):
        return self.__descriptive_text

    def attacks(self, attacked):
        if type(attacked) is Argument:
            self.__framework.add_argument(self)
            self.__framework.add_argument(attacked)
            attacked_id = attacked.id()
        elif type(attacked) is int:
            attacked_id = attacked
        else:
            print("Argument::attacks: Invalid type for argument!")
            return
        self.__framework.add_attack(self.__arg_id, attacked_id)

    def set_verifier(self, verifier):
        self.verifier_function = verifier
        pass

    def verifier(self):
        return self.verifier_function

    def verify(self, me, they):
        if self.verifier_function is not None:
            return self.verifier_function(me, they)


class PrivateArgument(Argument):
    def __init__(self, arg_id, descriptive_text, privacy_cost):
        super(PrivateArgument, self).__init__(arg_id, descriptive_text)
        self.privacy_cost = privacy_cost


class ArgumentationFramework:
    def __init__(self):
        self.__arguments = {}
        self.__attacks = {}
        self.__attacked_by = {}
        self.argument_strength = {}
        self.least_attacked = []

    def add_arguments(self, arguments: list):
        for arg in arguments:
            self.add_argument(arg)

    def arguments(self):
        return self.__arguments.values()

    def attacks(self):
        return self.__attacks

    def remove_argument(self, argument_id):
        if argument_id in self.__arguments.keys():
            del self.__arguments[argument_id]
        if argument_id in self.__attacks.keys():
            del self.__attacks[argument_id]
        for attacked_set in self.__attacks.values():
            if argument_id in attacked_set:
                attacked_set.remove(argument_id)
        for attacker_set in self.__attacked_by.values():
            if argument_id in attacker_set:
                attacker_set.remove(argument_id)

    def add_argument(self, argument):
        self.__arguments[argument.id()] = argument
        argument.set_framework(self)

    def add_attack(self, attacker_id, attacked_id):
        if self.__attacks.get(attacker_id, None) is None:
            self.__attacks[attacker_id] = set()
        if self.__attacked_by.get(attacked_id, None) is None:
            self.__attacked_by[attacked_id] = set()
        self.__attacks[attacker_id].add(attacked_id)
        self.__attacked_by[attacked_id].add(attacker_id)

    def arguments_that_attack(self, argument):
        if isinstance(argument, list):
            return self.arguments_that_attack_list(argument)
        return self.__attacked_by.get(argument, set())

    def arguments_that_attack_list(self, argument_list):
        result = set()
        for argument_id in argument_list:
            result.update(self.arguments_that_attack(argument_id))
        return result

    def arguments_attacked_by_list(self, argument_list):
        result = set()
        for argument_id in argument_list:
            result.update(self.arguments_attacked_by(argument_id))
        return result

    def arguments_attacked_by(self, argument):
        if isinstance(argument, list):
            return self.arguments_attacked_by_list(argument)
        return self.__attacks.get(argument, set())

    def argument(self, argument_id):
        return self.__arguments[argument_id]

    def compute_rank_arguments_occurrence(self, extension="PR"):
        """
        Calls ConArg as an external process to compute extensions.
        Returns a normalised "argument strength" value denoted by occurrences/num_extensions.
        :param extension: The type of extension to be considered.
        :return: Argument strengths as percentage of occurrence.
        """
        with open('sample.apx',  'w') as file:
            file.write(self.to_aspartix_id())

        # subprocess.run(["conarg_x64/conarg2", "-w dung", "-e admissible", "-c 4", "sample.apx"])
        result = subprocess.run(["mu-toksia/mu-toksia", "-p",  "EE-" + extension, "-fo",  "apx", "-f", "sample.apx"],
                                 capture_output=True, text=True)
        result_string = result.stdout
        result_string = result_string.replace("[", "")
        result_string = result_string.replace("]", "")
        result_string = result_string.replace("\t", "")
        match = result_string.split("\n")
        occurrences = {}
        for argument_obj in self.arguments():
            occurrences[argument_obj.id()] = 0
        for m in match:
            for argument_obj in self.arguments():
                arg_id = argument_obj.id()
                # FIXME: Finding individual digits in strings, flawed counting
                if str(arg_id) in m.split(","):
                    occurrences[arg_id] += 1
        num_extensions = len(match)

        argument_strength = {}
        for id, count in occurrences.items():
            if num_extensions == 0:
                num_extensions = 1
            argument_strength[id] = count / num_extensions

        self.argument_strength = argument_strength

    def rank_least_attacked_arguments(self):
        """
        :return: List of argument ids in ascending order of attacks received.
        """
        rank = {}
        for arg_id in self.__arguments:
            rank[arg_id] = 0
        for arg_id, attackers in self.__attacked_by.items():
            rank[arg_id] = len(attackers)
        self.least_attacked = sorted(rank, key=rank.get)

    def to_aspartix_id(self):
        text = ""
        for argument in self.__arguments:
            text += "arg({}).\n".format(argument)
        for attacker in self.__attacks.keys():
            for attacked in self.__attacks[attacker]:
                text += "att({},{}).\n".format(attacker, attacked)
        return text

    def to_aspartix_text(self):
        text = ""
        for argument_id in self.__arguments:
            arg_text = self.argument(argument_id).descriptive_text()
            text += "arg({}).\n".format(arg_text)
        for attacker_id in self.__attacks.keys():
            for attacked_id in self.__attacks[attacker_id]:
                attacker_text = self.argument(attacker_id).descriptive_text()
                attacked_text = self.argument(attacked_id).descriptive_text()
                text += "att({},{}).\n".format(attacker_text, attacked_text)
        return text





