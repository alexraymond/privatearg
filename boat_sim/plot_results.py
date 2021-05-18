import json
import random
import sys
import matplotlib.pyplot as plt

colours = 'bgrcmyk'


class ResultsManager:
    def __init__(self, results_filename):
        results_data = None
        with open(results_filename) as file:
            results_data = json.load(file)
        self.results = results_data["boats"]
        self.y_limit = results_data["y_limit"]

    def plot_animations(self, ids):
        pass

    def plot_trajectories(self, boat_ids=None, animated=False):
        if boat_ids is None:  # Plot all trajectories then.
            boat_ids = self.results.keys()
        if animated:
            self.plot_animations(boat_ids)
            return
        data = {}
        for boat_id in boat_ids:
            data[boat_id] = {}
            data[boat_id]["x"] = []
            data[boat_id]["y"] = []
            for snapshot in self.results[boat_id]:
                x = snapshot["x"]
                y = snapshot["y"]

                data[boat_id]["x"].append(x)
                data[boat_id]["y"].append(y)
            plt.ylim([0, self.y_limit*2])
            plt.plot(data[boat_id]["x"], data[boat_id]["y"], color=colours[int(boat_id) % len(colours)])
        plt.show()

#
# def main(argv):
#     results_filename = argv[0]
#     print(results_filename)
#     loader = ResultsManager(results_filename)
#     loader.plot_trajectories()
#
#
# if __name__ == "__main__":
#     main(sys.argv[1:])
