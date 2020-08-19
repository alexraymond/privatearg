
class Argument:
    def __init__(self, arg_id, descriptive_text):
        self.__arg_id = arg_id
        self.__descriptive_text = descriptive_text
        self.__framework = None
        self.__evidence = []
        self.__verifier = None

    def id(self):
        return self.__arg_id

    def set_framework(self, framework):
        self.__framework = framework

    def add_evidence(self, evidence):
        self.__evidence.append(evidence)

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

    def set_verifier(self, generator):
        self.__verifier = generator

    def verifier(self):
        return self.__verifier

    def verify(self, me, they):
        if self.__verifier is not None:
            return self.__verifier(me, they)


class PrivateArgument(Argument):
    def __init__(self, arg_id, descriptive_text, privacy_cost):
        super(PrivateArgument, self).__init__(arg_id, descriptive_text)
        self.privacy_cost = privacy_cost


class ArgumentationFramework:
    def __init__(self):
        self.__arguments = {}
        self.__attacks = {}
        self.__attacked_by = {}

    def add_arguments(self, arguments: list):
        for arg in arguments:
            self.add_argument(arg)

    def arguments(self):
        return self.__arguments.values()

    def attacks(self):
        return self.__attacks

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

    def arguments_that_attack(self, argument_id):
        return self.__attacked_by.get(argument_id, set())

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

    def arguments_attacked_by(self, argument_id):
        return self.__attacks.get(argument_id, set())

    def argument(self, argument_id):
        return self.__arguments[argument_id]

    def to_aspartix(self):
        text = ""
        for argument in self.__arguments:
            text += "arg({}).\n".format(argument)
        for attacker in self.__attacks.keys():
            for attacked in self.__attacks[attacker]:
                text += "att({},{}).\n".format(attacker, attacked)
        return text





