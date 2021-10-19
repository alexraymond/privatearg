import json
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats
import matplotlib.colors as mcolors

colours = list(mcolors.TABLEAU_COLORS.keys()) + list("bgrcmyk")

strategies = ["ArgStrategy.RANDOM_CHOICE_PRIVATE",
              "ArgStrategy.LEAST_COST_PRIVATE",
              "ArgStrategy.MOST_ATTACKS_PRIVATE",
              "ArgStrategy.LEAST_ATTACKERS_PRIVATE"]

labels = ['random', 'min_cost', 'offensive', 'defensive']

path = "results/experiment97/"

max_g = 60

boat_id = "7"

normal_data = {}
normal_trajectories = {}

subjective_data = {}
subjective_trajectories = {}

for strategy in strategies:
    for mode in ["normal", "subjective"]:
        with open(path + "{}-{}-g-{}-16-boats.json".format(mode, strategy, max_g)) as file:
            if mode == "normal":
                normal_data[strategy] = json.load(file)["boats"]
                normal_trajectories[strategy] = {"x": [], "y": []}
            else:
                subjective_data[strategy] = json.load(file)["boats"]
                subjective_trajectories[strategy] = {"x": [], "y": []}

with open(path + "objective-g-{}-16-boats.json".format(max_g)) as file:
    objective_data = json.load(file)["boats"]

objective_trajectory = {"x": [], "y": []}


def load_trajectory(x_container, y_container, results):
    for snapshot in results[boat_id]:
        x_container.append(snapshot["x"])
        y_container.append(snapshot["y"])


for strategy in strategies:
    normal = normal_trajectories[strategy]
    subjective = subjective_trajectories[strategy]
    load_trajectory(normal["x"], normal["y"], normal_data[strategy])
    load_trajectory(subjective["x"], subjective["y"], subjective_data[strategy])

load_trajectory(objective_trajectory["x"], objective_trajectory["y"], objective_data)

fig = plt.figure(figsize=(16, 9))
trajectories_plot = fig.add_subplot(1, 1, 1)

for mode in ["normal", "subjective"]:
    i = 0
    for strategy in strategies:
        current_colour = colours[i % len(colours)]
        if mode == "normal":
            trajectories_plot.plot(normal_trajectories[strategy]["x"], normal_trajectories[strategy]["y"],
                                   color=current_colour)
        else:
            trajectories_plot.plot(subjective_trajectories[strategy]["x"], subjective_trajectories[strategy]["y"],
                                   color=current_colour, linestyle='dashed')
        i += 1

trajectories_plot.plot(objective_trajectory["x"], objective_trajectory["y"], color="black", linestyle='dotted')
trajectories_plot.set_title('Trajectories')
trajectories_plot.set_xlabel('X coordinate')
trajectories_plot.set_ylabel('Y coordinate')
trajectories_plot.set_ylim([0, 1800])

labels = []
for mode in ["normal", "subjective"]:
    for strategy in ["random", "min_cost", "offensive", "defensive"]:
        labels.append("{} {}".format(mode, strategy))
labels.append("objective")

trajectories_plot.legend(labels)
plt.savefig('compare_trajectories.pdf')
plt.show()
