from agent import Agent

class BoatAgent(Agent):
    """
    Specialisation of the Agent class that loads a BoatCulture instead.
    """
    def __init__(self, id, max_privacy_budget=10):
        super().__init__(id, max_privacy_budget)
        self.properties = {}

    def __getitem__(self, item):
        return self.__dict__.get(item, None)

    # def __setitem__(self, key, value):
    #     self.__dict__[key] = value

    def culture_properties(self):
        if self.boat_culture is None:
            return None
        return self.boat_culture.__dict__.get("properties", None)

    def set_culture(self, culture):
        self.boat_culture = culture
        if self.culture_properties() is None:
            print("BoatAgent::set_culture: Culture {} has no properties.".format(culture.name))
            return
        for p, v in self.culture_properties().items():
            # Setting default culture properties and values to the agent.
            self.__setattr__(p, v)
            self.properties[p] = v
        self.sorted_properties = sorted(self.culture_properties().keys())


    def assign_property_value(self, property_, value):
        """
        Assigns a property value to an object attribute.
        Injecting culture properties such that they become part of the object attributes.
        :param property_: The property/attribute in question.
        :param value: The value associated with that property..
        """
        if type(property_) is not str:
            property_ = str(property_)
        self.__setattr__(property_, value)
        self.properties[property_] = value


