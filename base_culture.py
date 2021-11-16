from argument import ArgumentationFramework

class Culture:
    """
    Base Culture virtual interface. Meant to be extended with your own culture.
    """
    def __init__(self):
        self.AF = ArgumentationFramework()
        self.properties = {}
        self.name = None

    def create_arguments(self):
        pass

    def define_attacks(self):
        pass

    def arguments_that_attack_list(self, argument_list):
        return self.AF.arguments_that_attack_list(argument_list)

    def arguments_attacked_by_list(self, argument_list):
        return self.AF.arguments_attacked_by_list(argument_list)
