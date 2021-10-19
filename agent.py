import random
from private_culture import RandomCulture

class Agent:
    def __init__(self, id, max_privacy_budget=10):
        self.id = id
        self.properties = {}
        self.culture = None
        self.max_privacy_budget = max_privacy_budget
        self.privacy_budget = self.max_privacy_budget
        self.argued_with = []
        self.dialogue_results = {}
        self.unfair_perception_score = 0

    def set_max_privacy_budget(self, privacy_budget):
        self.max_privacy_budget = privacy_budget
        self.reset_privacy_budget()

    def add_result(self, pair, total_privacy_cost, winner, considered_unfair):
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
        self.culture = culture
        self.properties = self.culture.properties.copy()

        # Randomise values for random culture.
        if isinstance(self.culture, RandomCulture):
            for key, value in self.properties.items():
                self.properties[key] = random.randint(0, 1000)
                # dist = []
                # for i in range(21):
                #     if i > key:
                #         dist.append(random.randint(0, 1000))
                #     else:
                #         dist.append(0)
                # self.properties[key] = random.choice(dist)

    def has_argued_with(self, agent_id):
        return agent_id in self.argued_with

    def properties_to_dict(self):
        data = {}
        data["id"] = self.id
        data["properties"] = {}
        for key, value in self.properties.items():
            data["properties"][str(key)] = str(value)
        return data

    def results_to_dict(self):
        data = {}
        data["id"] = self.id
        data["max_privacy_budget"] = self.max_privacy_budget
        data["dialogue_results"] = self.dialogue_results
        return data
