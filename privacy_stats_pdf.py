import json
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats

with open('C:/work/projects/privatearg/experiment_data.json') as file:
    data = json.load(file)

strategies = ["ArgStrategy.RANDOM_CHOICE_PRIVATE",
                           "ArgStrategy.LEAST_COST_PRIVATE",
                           "ArgStrategy.MOST_ATTACKS_PRIVATE",
                           "ArgStrategy.LEAST_ATTACKERS_PRIVATE"]

labels = ['random', 'min_cost', 'offensive', 'defensive']

costs = {}
more_than = {}

max_g = 1000000
i = 0
for strategy in strategies:
    costs[strategy] = []
    for exp_id in data.keys():
        agents = data[exp_id]['results']['per_strategy'][strategy][str(max_g)]['agents']
        for agent in agents.keys():
            dialogues = agents[agent]['dialogue_results']
            for pair in dialogues.keys():
                i+=1
                costs[strategy].append(dialogues[pair]['total_privacy_cost'])


fig = plt.figure(figsize=(16, 9))
plot_costs = [costs[strategy] for strategy in strategies]

print("Len: {} {}".format(len(plot_costs[0]), i))

for strategy in strategies:
    more_than[strategy] = []
    for p in range(100):
        more_than[strategy].append(0)
        for i in range(len(costs[strategy])):
            if costs[strategy][i] >= p:
                more_than[strategy][p] += 1.0 / len(costs[strategy])

# box = fig.add_subplot(4, 1, 1)
# box.boxplot(plot_costs, positions=[0, 1, 2, 3], showfliers=True)
# print("Mean random: {}".format(np.mean(plot_costs[0])))
# print("Median random: {}".format(np.median(plot_costs[0])))
#
# print("Mean least_cost: {}".format(np.mean(plot_costs[1])))
# print("Median least_cost: {}".format(np.median(plot_costs[1])))
#
# print("Mean most_attacks: {}".format(np.mean(plot_costs[2])))
# print("Median most_attacks: {}".format(np.median(plot_costs[2])))
#
# print("Mean least_attackers: {}".format(np.mean(plot_costs[3])))
# print("Median least_attackers: {}".format(np.median(plot_costs[3])))
#
# random_plot = fig.add_subplot(4, 2, 3)
# random_plot.hist(plot_costs[0], bins=20)
# random_plot.set_title("Random")
# random_plot.set_xlim([0, 100])
#
# least_cost_plot = fig.add_subplot(4, 2, 4)
# least_cost_plot.hist(plot_costs[1], bins=20)
# least_cost_plot.set_title("Least cost")
# least_cost_plot.set_xlim([0, 100])
#
# most_attacks_plot = fig.add_subplot(4, 2, 5)
# most_attacks_plot.hist(plot_costs[2], bins=20)
# most_attacks_plot.set_title("Most attacks")
# most_attacks_plot.set_xlim([0, 100])
#
# least_attackers_plot = fig.add_subplot(4, 2, 6)
# least_attackers_plot.hist(plot_costs[3], bins=20)
# least_attackers_plot.set_title("Least attackers")
# least_attackers_plot.set_xlim([0, 100])

prob_plot = fig.add_subplot(1, 1, 1)
x = [x for x in range(100)]
prob_plot.plot(x, more_than[strategies[0]], linewidth=2.0)
prob_plot.plot(x, more_than[strategies[1]], linewidth=2.0)
prob_plot.plot(x, more_than[strategies[2]], linewidth=2.0)
prob_plot.plot(x, more_than[strategies[3]], linewidth=2.0)
prob_plot.legend(labels)
prob_plot.set_title("Probability that a dialogue will cost more than z.")
prob_plot.set_xlabel("z")
prob_plot.set_ylabel("Probability")
prob_plot.grid()
plt.savefig('privacy_efficiency.pdf')

for i in range(len(strategies)):
    for j in range(i+1, len(strategies)):
        mw_less, p_less = scipy.stats.ttest_ind(plot_costs[i], plot_costs[j], equal_var=False, alternative='less')

        mw_greater, p_greater = scipy.stats.ttest_ind(plot_costs[i], plot_costs[j], equal_var=False, alternative='greater')

        print("MW less {} vs {}. U = {}, p = {}".format(labels[i], labels[j], mw_less, p_less))
        print("MW greater {} vs {}. U = {}, p = {}".format(labels[i], labels[j], mw_greater, p_greater))



# plot.set_xticks(['random', 'least_cost', 'most_attacks', 'least_attackers'])

plt.show()

