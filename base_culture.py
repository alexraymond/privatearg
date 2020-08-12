from argument import ArgumentationFramework

class Culture:
    def __init__(self):
        self.argumentation_framework = ArgumentationFramework()
        self.properties = {}
        self.name = None

        # self.create_arguments()
        # self.define_attacks()

    def create_arguments(self):
        pass

    def define_attacks(self):
        pass

    def arguments_that_attack_list(self, argument_list):
        return self.argumentation_framework.arguments_that_attack_list(argument_list)

    def arguments_attacked_by_list(self, argument_list):
        return self.argumentation_framework.arguments_attacked_by_list(argument_list)
