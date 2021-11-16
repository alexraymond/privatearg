import subprocess
import string
import re
# import graph_tool.all as gt

class Argument:
    """
    Base Argument class. An ArgumentationFramework is composed of multiple Arguments and attack relationships
    between them. Every argument has a verifier function that is injected from the culture.
    """
    def __init__(self, arg_id, descriptive_text):
        self.__arg_id = arg_id
        self.descriptive_text = descriptive_text
        self.__framework = None
        self.evidence = []
        self.verifier_function = None

    def id(self):
        return self.__arg_id

    def set_framework(self, framework):
        self.__framework = framework

    def add_evidence(self, evidence):
        self.evidence.append(evidence)

    def attacks(self, attacked):
        """
        Establishes an attack relationship between arguments a and b.
        Usage is in the form a.attacks(b).
        :param attacked: Argument b in the example above.
        """
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

    def verifier(self):
        return self.verifier_function

    def verify(self, me, they):
        """
        This is the act of calling the externally-injected verifier function.
        In this case, the verifier function must accept two arguments, representing the two agents
        in the dialogue.
        :param me: The agent to whom the perspective of the argument applies. The 'I' in 'I am older than you.'
        :param they: The other agent. The 'you' in 'I am older than you.'
        :return: True if the argument holds. False otherwise.
        """
        if self.verifier_function is not None:
            return self.verifier_function(me, they)


class PrivateArgument(Argument):
    """
    A specialisation of the Argument class to support privacy-aware dialogues.
    """
    def __init__(self, arg_id, privacy_cost, descriptive_text="", hypothesis_text="", verified_fact_text=""):
        super(PrivateArgument, self).__init__(arg_id, descriptive_text)
        self.privacy_cost = privacy_cost
        self.hypothesis_text = hypothesis_text
        self.verified_fact_text = verified_fact_text
        self.hypothesis_verifier = None
        self.fact_verifier = None


class ArgumentationFramework:
    """
    An argumentation framework is represented as a directed graph on Arguments.
    """
    def __init__(self):
        self.all_arguments = {}
        self.all_attacks = {}
        self.all_attacked_by = {}
        self.argument_strength = {}
        self.least_attacked = []
        self.strongest_attackers = []

    def add_arguments(self, arguments: list):
        for arg in arguments:
            self.add_argument(arg)

    def arguments(self):
        return self.all_arguments.values()

    def argument_ids(self):
        return self.all_arguments.keys()

    def attacks(self):
        return self.all_attacks

    def attacked_by(self):
        return self.all_attacked_by

    def remove_argument(self, argument_id):
        if argument_id in self.all_arguments.keys():
            del self.all_arguments[argument_id]
        if argument_id in self.all_attacks.keys():
            del self.all_attacks[argument_id]
        if argument_id in self.all_attacked_by.keys():
            del self.all_attacked_by[argument_id]
        for id, attacked_set in self.all_attacks.items():
            if argument_id in attacked_set:
                attacked_set.remove(argument_id)
        for id, attacker_set in self.all_attacked_by.items():
            if argument_id in attacker_set:
                attacker_set.remove(argument_id)

    def add_argument(self, argument):
        self.all_arguments[argument.id()] = argument
        argument.set_framework(self)

    def add_attack(self, attacker_id, attacked_id):
        if self.all_attacks.get(attacker_id, None) is None:
            self.all_attacks[attacker_id] = set()
        if self.all_attacked_by.get(attacked_id, None) is None:
            self.all_attacked_by[attacked_id] = set()
        self.all_attacks[attacker_id].add(attacked_id)
        self.all_attacked_by[attacked_id].add(attacker_id)

    def arguments_that_attack(self, argument):
        """
        Returns all other arguments that attack the parameter argument.
        :param argument: The reference argument.
        :return: Set of arguments that attack it.
        """
        if isinstance(argument, list):
            return self.arguments_that_attack_list(argument)
        return self.all_attacked_by.get(argument, set())

    def arguments_that_attack_list(self, argument_list):
        """
        Same as arguments_that_attack, but concerning a list of arguments.
        :param argument_list: The list of arguments that are attacked.
        :return: Set of arguments that attack it.
        """
        result = set()
        for argument_id in argument_list:
            result.update(self.arguments_that_attack(argument_id))
        return result

    def arguments_attacked_by_list(self, argument_list):
        """
        The inverse of arguments_that_attack_list.
        :param argument_list: The list of arguments that attack.
        :return: Set of arguments that is attacked by this list.
        """
        result = set()
        for argument_id in argument_list:
            result.update(self.arguments_attacked_by(argument_id))
        return result

    def arguments_attacked_by(self, argument):
        """
        Returns all other arguments that are attacked by the parameter argument.
        :param argument: The reference argument.
        :return: Set of arguments are attacked by it.
        """
        if isinstance(argument, list):
            return self.arguments_attacked_by_list(argument)
        return self.all_attacks.get(argument, set())

    def argument(self, argument_id):
        return self.all_arguments[argument_id]

    def compute_rank_arguments_occurrence(self, semantics="EE-PR"):
        """
        Calls ConArg as an external process to compute extensions.
        Returns a normalised "argument strength" value denoted by occurrences/num_extensions.
        :param semantics: The type of semantics to be considered.
        :return: Argument strengths as percentage of occurrence.
        """
        result_string = self.run_solver(semantics)
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

    def run_solver(self, semantics="EE-PR", arg_str=""):
        """
        Runs the mu-toksia solver to check if an argument is part of the extension given by the semantics.
        :param semantics: The type of semantics to be considered.
        :param arg_str: The string defining the argument.
        :return: stdout output of the solver (likely "YES" or "NO").
        """
        with open('sample.apx',  'w') as file:
            file.write(self.to_aspartix_id())

        # subprocess.run(["conarg_x64/conarg2", "-w dung", "-e admissible", "-c 4", "sample.apx"])
        if not arg_str:
            result = subprocess.run(["mu-toksia/mu-toksia.exe", "-p", semantics, "-fo", "apx", "-f", "sample.apx"],
                                    capture_output=True, text=True)
        else:
            result = subprocess.run(["mu-toksia/mu-toksia.exe", "-p", semantics, "-fo", "apx", "-f", "sample.apx",
                                     "-a", arg_str],
                                    capture_output=True, text=True)

        if result.stderr:  # some error
            raise RuntimeError('Failed to compute extension: {}'.format(result.stderr))

        return result.stdout

    def rank_least_attacked_arguments(self):
        """
        :return: List of argument ids in ascending order of attacks received.
        """
        rank = {}
        for arg_id in self.all_arguments:
            rank[arg_id] = 0
        for arg_id, attackers in self.all_attacked_by.items():
            rank[arg_id] = len(attackers)
        self.least_attacked = sorted(rank, key=rank.get)

    def rank_strongest_attacker_arguments(self):
        """
        :return: List of argument ids in ascending order of attacks received.
        """
        rank = {}
        for arg_id in self.all_arguments:
            rank[arg_id] = 0
        for arg_id, attacks in self.all_attacks.items():
            rank[arg_id] = len(attacks)
        self.strongest_attackers = sorted(rank, key=rank.get, reverse=True)

    def to_aspartix_id(self):
        text = ""
        for argument in self.all_arguments:
            text += "arg({}).\n".format(argument)
        for attacker in self.all_attacks.keys():
            for attacked in self.all_attacks[attacker]:
                text += "att({},{}).\n".format(attacker, attacked)
        return text

    def to_aspartix_text(self):
        text = ""
        for argument_id in self.all_arguments:
            arg_text = self.argument(argument_id).descriptive_text
            text += "arg({}).\n".format(arg_text)
        for attacker_id in self.all_attacks.keys():
            for attacked_id in self.all_attacks[attacker_id]:
                attacker_text = self.argument(attacker_id).descriptive_text
                attacked_text = self.argument(attacked_id).descriptive_text
                text += "att({},{}).\n".format(attacker_text, attacked_text)
        return text






