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
        self.unfair_perception_score = 0

    def set_max_privacy_budget(self, privacy_budget):
        self.max_privacy_budget = privacy_budget
        self.reset_privacy_budget()

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