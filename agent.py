import random
from private_culture import RandomCulture

class Agent:
    """
    Dialogue agent.
    Each agent is associated to the present culture and holds the history of dialogues with other agents.
    """
    def __init__(self, id, max_privacy_budget=10):
        """
        Initialises the agent.
        :param id: Agent ID.
        :param max_privacy_budget: Maximum privacy budget allocated to this agent.
        """
        self.id = id
        self.properties = {}
        self.culture = None
        self.max_privacy_budget = max_privacy_budget
        self.privacy_budget = self.max_privacy_budget
        # List of agents that agent has interacted with.
        self.argued_with = []
        # Results of dialogical interactions in the form {pair, result}
        self.dialogue_results = {}
        # How many dialogues ended with the perception of unfairness.
        self.unfair_perception_score = 0

    def set_max_privacy_budget(self, privacy_budget):
        self.max_privacy_budget = privacy_budget
        self.reset_privacy_budget()

    def add_result(self, pair, total_privacy_cost, winner, considered_unfair):
        """
        Adds a dialogue result to the results dictionary.
        """
        defender, challenger = pair
        pair_ids = (defender.id, challenger.id)
        self.dialogue_results[str(pair_ids)] = {}
        results = self.dialogue_results[str(pair_ids)]
        results["total_privacy_cost"] = total_privacy_cost
        results["winner"] = winner
        results["considered_unfair"] = considered_unfair

    def reset_privacy_budget(self):
        self.privacy_budget = self.max_privacy_budget

    def set_culture(self, culture):
        """
        Sets the culture of the agent.
        """
        self.culture = culture
        self.properties = self.culture.properties.copy()

        # Randomise values for random culture.
        if isinstance(self.culture, RandomCulture):
            for key, value in self.properties.items():
                self.properties[key] = random.randint(0, 1000)


    def has_argued_with(self, agent_id):
        return agent_id in self.argued_with

    def properties_to_dict(self):
        """
        :return: Dict containing agent properties.
        """
        data = {}
        data["id"] = self.id
        data["properties"] = {}
        for key, value in self.properties.items():
            data["properties"][str(key)] = str(value)
        return data

    def results_to_dict(self):
        """
        :return: Dict containing dialogue results.
        """
        data = {}
        data["id"] = self.id
        data["max_privacy_budget"] = self.max_privacy_budget
        data["dialogue_results"] = self.dialogue_results
        return data
