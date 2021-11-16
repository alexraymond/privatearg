import json
import random
import sys
import os
import math
import numpy as np
import similaritymeasures as sm
import scipy.stats
from scipy import signal
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
from matplotlib.cbook import boxplot_stats
import pandas as pd
import seaborn as sns
sns.set_palette("colorblind")
plt.rc('axes', axisbelow=True)

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
sns.set(style="whitegrid", font_scale=2)
textfont = {'fontname': 'Linux Libertine'}
ttfont = {'fontname': 'Inconsolata'}
plt.rcParams['font.family'] = 'Linux Libertine'
# matplotlib.rc('font', family='Linux Libertine')

colours = list("bgrcmyk") + list(mcolors.TABLEAU_COLORS.keys())
g = 9.81  # m/s^2

def get_boxplot_data(labels, bp):
    rows_list = []

    for i in range(len(labels)):
        dict1 = {}
        dict1['label'] = labels[i]
        dict1['lower_whisker'] = bp['whiskers'][i*2].get_ydata()[1]
        dict1['lower_quartile'] = bp['boxes'][i].get_ydata()[1]
        dict1['median'] = bp['medians'][i].get_ydata()[1]
        dict1['mean'] = bp['means'][i].get_ydata()[0]
        dict1['upper_quartile'] = bp['boxes'][i].get_ydata()[2]
        dict1['upper_whisker'] = bp['whiskers'][(i*2)+1].get_ydata()[1]
        rows_list.append(dict1)

    return pd.DataFrame(rows_list)


class TextColour:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

load_last = True

class MultiTrialResults:
    def __init__(self, g):
        self.results_folder = "results_g{}/".format(g)
        self.max_g = g
        self.directories = [x[0] for x in os.walk(self.results_folder)]
        self.strategies = ["ArgStrategy.RANDOM_CHOICE_PRIVATE",
                           "ArgStrategy.LEAST_COST_PRIVATE",
                           "ArgStrategy.MOST_ATTACKS_PRIVATE",
                           "ArgStrategy.LEAST_ATTACKERS_PRIVATE"]

        self.full_results = {}
        self.final_results = {}
        self.display_results = {}

        if load_last:
            with open('final_results_g{}.json'.format(g)) as final_results_file:
                self.display_results = json.load(final_results_file)
        else:
            print("Calculating comparisons...")
            self.initialise()
            self.calculate_comparisons()
            self.pre_plot_results()
            with open('new_final_results_g{}.json'.format(g), 'w') as final_results_file:
                json.dump(self.display_results, final_results_file, indent=4)

        self.plot_results()

    def initialise(self):
        sim_types = ["normal", "subjective", "objective"]
        # Important so we don't run out of memory. A value of 1 = sample one frame per data point.
        self.trajectory_sample_rate = 20
        for directory in self.directories:
            directory = directory.replace("results_g{}/".format(self.max_g), "")
            if "experiment" not in directory:
                continue
            self.full_results = {directory: {}}
            self.final_results[directory] = {}
            for sim_type in sim_types:
                print("Loading {} {}...".format(sim_type, directory))
                self.full_results[directory][sim_type] = {}
                self.final_results[directory][sim_type] = {}
                if sim_type != "objective":
                    for strategy in self.strategies:
                        self.full_results[directory][sim_type][strategy] = {}
                        filename = self.results_folder + directory + "/{}-{}-g-{}-16-boats.json".format(sim_type,
                                                                                                        strategy,
                                                                                                        self.max_g)
                        with open(filename) as file:
                            self.full_results[directory][sim_type][strategy] = json.load(file)
                            full_result = self.full_results[directory][sim_type][strategy]
                            self.final_results[directory][sim_type][strategy] = self.get_stats(full_result)
                else:
                    filename = self.results_folder + directory + "/{}-g-{}-16-boats.json".format(sim_type, self.max_g)
                    with open(filename) as file:
                        self.full_results[directory][sim_type] = json.load(file)
                        full_result = self.full_results[directory][sim_type]
                        self.final_results[directory][sim_type] = self.get_stats(full_result)

    def plot_results(self):

        def add_data(plot, category, strategies, stat="tt", title="", xlabel="", ylabel="", ylim=None):
            index = 0
            labels = []
            plot.set_title(category if not title else title, **textfont)
            short_names = {"ArgStrategy.RANDOM_CHOICE_PRIVATE": "random",
                           "ArgStrategy.LEAST_COST_PRIVATE": "min_cost",
                           "ArgStrategy.MOST_ATTACKS_PRIVATE": "offensive",
                           "ArgStrategy.LEAST_ATTACKERS_PRIVATE": "defensive"}
            data = []
            df = pd.DataFrame()
            for strategy in strategies:
                label = short_names[strategy]
                labels.append(label)
                data.append(self.display_results[category][strategy])
                df[label] = pd.Series(self.display_results[category][strategy])
                # temp_df = pd.DataFrame({label: self.display_results[category][strategy]})
                # df.append(temp_df)

            print("\n\n{}***** {} *****{}".format(TextColour.BOLD, category, TextColour.END))

            # df = pd.DataFrame(list(zip(*data)))
            print("Dataframe")
            print(df)

            asterisks = {}

            def get_asterisks(p):
                s = ""
                s += '*' if p <= 0.05 else ''
                s += '*' if p <= 0.01 else ''
                s += '*' if p <= 0.001 else ''
                return s


            for i in range(len(data)):
                print("[{}]".format(labels[i]))
                print("Sample size {} ({}): {}".format(category, labels[i], len(data[i])))
                print("Mean {} ({}): {}".format(category, labels[i], np.mean(data[i])))
                print("Median {} ({}): {}".format(category, labels[i], np.median(data[i])))
                print("SD {} ({}): {}".format(category, labels[i], np.std(data[i])))
                print("Variance {} ({}): {}".format(category, labels[i], np.var(data[i])))
                for j in range(len(data)):
                    key = labels[i]+labels[j]
                    asterisks[key] = ""
                    if stat == "mw":
                        mw_2s, p_mw_2s = scipy.stats.mannwhitneyu(data[i], data[j], alternative='two-sided')
                        # if p_mw_2s < 0.05:
                        print("{}: MW two-sided {} vs {}. U = {}, p = {}".format(category, labels[i], labels[j], mw_2s, p_mw_2s))
                        mw_less, p_less = scipy.stats.mannwhitneyu(x=data[i], y=data[j], alternative='less')
                        # if p_less < 0.05:
                        print("{}: MW less {} vs {}. U = {}, p = {}".format(category, labels[i], labels[j], mw_less, p_less))
                        mw_greater, p_greater = scipy.stats.mannwhitneyu(x=data[i], y=data[j], alternative='greater')
                        # if p_greater < 0.05:
                        print("{}: MW greater {} vs {}. U = {}, p = {}".format(category, labels[i], labels[j], mw_greater, p_greater))
                        print("\n")
                    elif stat == "tt":
                        tt_2s, p_tt_2s = scipy.stats.ttest_ind(data[i], data[j], equal_var=False, alternative='two-sided')
                        # if p_tt_2s < 0.05:
                        print("{}: TT two-sided {} vs {}. T = {:.2f}, p = {}".format(category, labels[i], labels[j], tt_2s,
                                                                                 p_tt_2s))
                        tt_less, p_less = scipy.stats.ttest_ind(data[i], data[j], equal_var=False, alternative='less')
                        if p_less <= 0.05 and p_tt_2s <= 0.05:
                            asterisks[key] = get_asterisks(p_less)
                        print("{}: tt less {} vs {}. T = {:.2f}, p = {}".format(category, labels[i], labels[j], tt_less,
                                                                            p_less))
                        tt_greater, p_greater = scipy.stats.ttest_ind(data[i], data[j], equal_var=False, alternative='greater')
                        # if p_greater < 0.05:
                        print(
                            "{}: tt greater {} vs {}. T = {:.2f}, p = {}".format(category, labels[i], labels[j], tt_greater,
                                                                             p_greater))
                        print("\n")
                    elif stat == "anova":
                        anova_2s, p_anova_2s = scipy.stats.kruskal(data[i], data[j])
                        # if p_anova_2s < 0.05:
                        print("{}: friedman {} vs {}. F = {:.2f}, p = {}".format(category, labels[i], labels[j], anova_2s,
                                                                                 p_anova_2s))
                        # anova_less, p_less = scipy.stats.f_oneway(data[i], data[j])
                        # # if p_less < 0.05:
                        # print("{}: anova less {} vs {}. F = {:.2f}, p = {}".format(category, labels[i], labels[j], anova_less,
                        #                                                     p_less))
                        # anova_greater, p_greater = scipy.stats.f_oneway(data[i], data[j], equal_var=True, alternative='greater')
                        # # if p_greater < 0.05:
                        # print(
                        #     "{}: anova greater {} vs {}. F = {:.2f}, p = {}".format(category, labels[i], labels[j], anova_greater,
                        #                                                      p_greater))
                        print("\n")

            # bp = plot.boxplot(data, positions=[0, 1, 2, 3], showmeans=True, showfliers=False)
            df_flat = df[["random", "min_cost", "offensive", "defensive"]].melt().assign(x='vars')
            df_flat["strategy"] = df_flat[["variable"]].apply(lambda x: "_".join(x), axis=1)
            # df_flat["combination"] = df_flat[["variable", "strategy"]].apply(lambda x: "_".join(x), axis=1)

            df12 = df[["random", "min_cost"]].melt().assign(x='vars')
            df12["position"] = 0

            df13 = df[["random", "offensive"]].melt().assign(x='vars')
            df13["position"] = 1

            df14 = df[["random", "defensive"]].melt().assign(x='vars')
            df14["position"] = 2

            df23 = df[["min_cost", "offensive"]].melt().assign(x='vars')
            df23["position"] = 3

            df24 = df[["min_cost", "defensive"]].melt().assign(x='vars')
            df24["position"] = 4

            df34 = df[["offensive", "defensive"]].melt().assign(x='vars')
            df34["position"] = 5

            palette = sns.color_palette("colorblind")

            order = [0, 1, 2, 3, 4, 5]

            def plot_multiple(dfs, asterisks):
                i = 0
                strategy_colours = {"random": palette[0], "min_cost": palette[1], "offensive": palette[2], "defensive": palette[3]}
                for tdf in dfs:
                    sns.violinplot(data=tdf, x='position', y='value', order=order,
                                   palette=strategy_colours,
                                   hue='variable', split=True, scale="count", cut=0, saturation=0.5, inner=None)
                    types = tdf["variable"].unique()
                    i = 0
                    for t in types:
                        bdf = tdf.loc[tdf['variable'] == t]
                        delta = 0.15
                        bp_xpos = bdf['position'].iloc[0]
                        bp_xpos += delta if i else -delta

                        series = bdf['value'].to_numpy()
                        bp = plot.boxplot(series, positions=[bp_xpos], showfliers=False,
                        showcaps=True,widths=0.12, patch_artist=True,
                        boxprops=dict(color='k', facecolor=strategy_colours[t], linewidth=1.5),
                        whiskerprops=dict(color=strategy_colours[t], linewidth=1.5),
                        medianprops=dict(color="k", linewidth=1.5))

                        key = types[0]+types[1] if t == types[0] else types[1]+types[0]
                        floating_text = asterisks[key]
                        upper_whisker = bp['whiskers'][1].get_ydata()[1]
                        lentext = len(floating_text)
                        textdelta = 0.11 * lentext
                        plot.text(bp_xpos - (textdelta if i == 0 else 0), upper_whisker + 1, floating_text,
                                  fontweight='extra bold', fontsize=24, color=strategy_colours[t])
                        i += 1


            plot_multiple([df12, df13, df14, df23, df24, df34], asterisks)
            plot.set_xlabel(xlabel)
            plot.set_xticks([])
            plot.set_ylabel(ylabel)
            plot.set_ylim(ylim)
            custom_lines = [Line2D([0], [0], color=palette[0], lw=12),
                            Line2D([0], [0], color=palette[1], lw=12),
                            Line2D([0], [0], color=palette[2], lw=12),
                            Line2D([0], [0], color=palette[3], lw=12)]

            if category == "NTS_frechet":
                plot.legend(custom_lines, ['random', 'min_cost', 'offensive', 'defensive'], prop={'family':'Inconsolata', 'size':24},
                            loc='lower center', bbox_to_anchor=(0.5, 1.04),
                            ncol=4, fancybox=True, shadow=True
                            )
            else:
                plot.get_legend().remove()

            plt.grid(color='lightgray', linestyle='dashed')
            print("Data for {}".format(plot.get_title()))
            # print(get_boxplot_data(labels, bp))

        ############################################################
        # Plotting kinematics figure.

        miny = 0

        kinematics_fig = plt.figure(figsize=(27, 16))

        # acc_plot = kinematics_fig.add_subplot(2, 3, 1)
        # add_data(acc_plot, "acc_area", self.strategies, title="Mean area under acceleration curve")

        lay_plot = kinematics_fig.add_subplot(2, 3, 1)
        add_data(lay_plot, category="lay_area", strategies=self.strategies, title="Lateral acceleration", ylabel="Integral of lat. acceleration dt", ylim=[miny, 900])

        yaw_plot = kinematics_fig.add_subplot(2, 3, 2)
        add_data(yaw_plot, category="yaw_area", strategies=self.strategies, title="Yaw rate", ylabel="Integral of yaw rate dt", ylim=[miny, 400])

        # jerk_plot = kinematics_fig.add_subplot(2, 3, 4)
        # add_data(jerk_plot, "jerk_area", self.strategies, title="Mean area under jerk curve")

        lat_jerk_plot = kinematics_fig.add_subplot(2, 3, 3)
        add_data(lat_jerk_plot, category="lat_jerk_area", strategies=self.strategies, title="Lateral jerk", ylabel="Integral of lat. jerk dt", ylim=[miny, 1800])

        ############################################################
        # Plotting normal to objective figure.
        # NTO_fig = plt.figure(figsize=(20, 16))

        # NTO_pcm = NTO_fig.add_subplot(2, 3, 1)
        # add_data(NTO_pcm, "NTO_pcm", self.strategies)

        NTO_frechet = kinematics_fig.add_subplot(2, 3, 4)
        add_data(NTO_frechet, category="NTO_frechet", title="Objective Unfairness", strategies=self.strategies, ylabel="Fréchet distance (m)", ylim=[miny, 800])

        # NTO_area = NTO_fig.add_subplot(2, 3, 3)
        # add_data(NTO_area, "NTO_area", self.strategies)
        #
        # NTO_curve = NTO_fig.add_subplot(2, 3, 4)
        # add_data(NTO_curve, "NTO_curve_length", self.strategies)
        #
        # NTO_dtw = NTO_fig.add_subplot(2, 3, 5)
        # add_data(NTO_dtw, "NTO_dtw", self.strategies)

        ############################################################
        # Plotting normal to subjective figure.
        # NTS_fig = plt.figure(3, figsize=(20, 16))

        # NTS_pcm = NTS_fig.add_subplot(2, 3, 1)
        # add_data(NTS_pcm, "NTS_pcm", self.strategies)

        NTS_frechet = kinematics_fig.add_subplot(2, 3, 5)
        add_data(NTS_frechet, category="NTS_frechet", title="Subjective Unfairness", strategies=self.strategies, ylabel="Fréchet distance (m)", ylim=[miny, 300])

        # NTS_area = NTS_fig.add_subplot(2, 3, 3)
        # add_data(NTS_area, "NTS_area", self.strategies)
        #
        # NTS_curve = NTS_fig.add_subplot(2, 3, 4)
        # add_data(NTS_curve, "NTS_curve_length", self.strategies)
        #
        # NTS_dtw = NTS_fig.add_subplot(2, 3, 5)
        # add_data(NTS_dtw, "NTS_dtw", self.strategies)

        ############################################################
        # Plotting subjective to objective figure.
        # STO_fig = plt.figure(4, figsize=(20, 16))
        # STO_pcm = STO_fig.add_subplot(2, 3, 1)
        # add_data(STO_pcm, "STO_pcm", self.strategies)

        STO_frechet = kinematics_fig.add_subplot(2, 3, 6)
        add_data(STO_frechet, category="STO_frechet", title="Subjectivity Gap", strategies=self.strategies, ylabel="Fréchet distance (m)", ylim=[miny, 800])

        # STO_area = STO_fig.add_subplot(2, 3, 3)
        # add_data(STO_area, "STO_area", self.strategies)
        #
        # STO_curve = STO_fig.add_subplot(2, 3, 4)
        # add_data(STO_curve, "STO_curve_length", self.strategies)
        #
        # STO_dtw = STO_fig.add_subplot(2, 3, 5)
        # add_data(STO_dtw, "STO_dtw", self.strategies)

        ############################################################
        # Plotting.

        # qq_fig = plt.figure(5, figsize=(12,12))
        # qq_plot = STO_fig.add_subplot(2,3,6)
        # scipy.stats.probplot(self.display_results["STO_frechet"]["ArgStrategy.LEAST_ATTACKERS_PRIVATE"], dist="norm", plot=qq_plot)

        # plt.gca().set_axis_off()
        # plt.subplots_adjust(top=1, bottom=0, right=1, left=0,
        #                     hspace=0, wspace=0)
        # plt.margins(0, 0)
        # plt.gca().xaxis.set_major_locator(plt.NullLocator())
        # plt.gca().yaxis.set_major_locator(plt.NullLocator())
        plt.subplots_adjust(top=0.95)
        plt.savefig("plots.pdf", bbox_inches='tight',
                    pad_inches=0)
        plt.savefig('plots.jpg', dpi=600, bbox_inches='tight',
                    pad_inches=0)
        plt.savefig('plots.svg', bbox_inches='tight',
                    pad_inches=0)
        plt.show()

    def pre_plot_results(self):
        def add_category(base_dict, category_name, strategies):
            base_dict[category_name] = {}
            for strategy in strategies:
                base_dict[category_name][strategy] = []

        add_category(self.display_results, "acc_area", self.strategies)
        add_category(self.display_results, "jerk_area", self.strategies)
        add_category(self.display_results, "lay_area", self.strategies)
        add_category(self.display_results, "lat_jerk_area", self.strategies)
        add_category(self.display_results, "yaw_area", self.strategies)
        add_category(self.display_results, "NTO_pcm", self.strategies)
        add_category(self.display_results, "NTO_frechet", self.strategies)
        add_category(self.display_results, "NTO_area", self.strategies)
        add_category(self.display_results, "NTO_curve_length", self.strategies)
        add_category(self.display_results, "NTO_dtw", self.strategies)
        add_category(self.display_results, "NTS_pcm", self.strategies)
        add_category(self.display_results, "NTS_frechet", self.strategies)
        add_category(self.display_results, "NTS_area", self.strategies)
        add_category(self.display_results, "NTS_curve_length", self.strategies)
        add_category(self.display_results, "NTS_dtw", self.strategies)
        add_category(self.display_results, "STO_pcm", self.strategies)
        add_category(self.display_results, "STO_frechet", self.strategies)
        add_category(self.display_results, "STO_area", self.strategies)
        add_category(self.display_results, "STO_curve_length", self.strategies)
        add_category(self.display_results, "STO_dtw", self.strategies)

        for category in self.display_results.keys():
            for strategy in self.strategies:
                for experiment in self.final_results.values():
                    for boat_id in experiment["normal"][strategy]:
                        if category in experiment["normal"][strategy][boat_id]:
                            self.display_results[category][strategy].append(
                                experiment["normal"][strategy][boat_id][category])

                        # self.display_results["NTO_pcm"][strategy].append(
                        #     experiment["normal_to_objective"][strategy][boat_id]["pcm"])
                        self.display_results["NTO_frechet"][strategy].append(
                            experiment["normal_to_objective"][strategy][boat_id]["frechet"])
                        # self.display_results["NTO_area"][strategy].append(
                        #     experiment["normal_to_objective"][strategy][boat_id]["area"])
                        # self.display_results["NTO_curve_length"][strategy].append(
                        #     experiment["normal_to_objective"][strategy][boat_id]["curve_length"])
                        # self.display_results["NTO_dtw"][strategy].append(
                        #     experiment["normal_to_objective"][strategy][boat_id]["dtw"])

                        # self.display_results["NTS_pcm"][strategy].append(
                        #     experiment["normal_to_subjective"][strategy][boat_id]["pcm"])
                        self.display_results["NTS_frechet"][strategy].append(
                            experiment["normal_to_subjective"][strategy][boat_id]["frechet"])
                        # self.display_results["NTS_area"][strategy].append(
                        #     experiment["normal_to_subjective"][strategy][boat_id]["area"])
                        # self.display_results["NTS_curve_length"][strategy].append(
                        #     experiment["normal_to_subjective"][strategy][boat_id]["curve_length"])
                        # self.display_results["NTS_dtw"][strategy].append(
                        #     experiment["normal_to_subjective"][strategy][boat_id]["dtw"])

                        # self.display_results["STO_pcm"][strategy].append(
                        #     experiment["subjective_to_objective"][strategy][boat_id]["pcm"])
                        self.display_results["STO_frechet"][strategy].append(
                            experiment["subjective_to_objective"][strategy][boat_id]["frechet"])
                        # self.display_results["STO_area"][strategy].append(
                        #     experiment["subjective_to_objective"][strategy][boat_id]["area"])
                        # self.display_results["STO_curve_length"][strategy].append(
                        #     experiment["subjective_to_objective"][strategy][boat_id]["curve_length"])
                        # self.display_results["STO_dtw"][strategy].append(
                        #     experiment["subjective_to_objective"][strategy][boat_id]["dtw"])

    def calculate_comparisons(self):
        distances = []
        for directory in self.final_results.keys():
            print("Comparative data for {}...".format(directory))
            experiment = self.final_results[directory]
            experiment["normal_to_objective"] = {}
            experiment["normal_to_subjective"] = {}
            experiment["subjective_to_objective"] = {}
            for boat_id in experiment["objective"].keys():
                print("Experiment {}. Boat {}/16.".format(directory, boat_id))
                objective_x_data = experiment["objective"][boat_id]["x"]
                objective_y_data = experiment["objective"][boat_id]["y"]
                objective_trajectory = np.zeros((len(objective_x_data), 2))
                objective_trajectory[:, 0] = objective_x_data
                objective_trajectory[:, 1] = objective_y_data
                for strategy in self.strategies:
                    distance = {}
                    distance["strategy"] = strategy
                    distance["boat_id"] = boat_id
                    distance["experiment"] = directory
                    normal_x_data = experiment["normal"][strategy][boat_id]["x"]
                    normal_y_data = experiment["normal"][strategy][boat_id]["y"]
                    normal_trajectory = np.zeros((len(normal_x_data), 2))
                    normal_trajectory[:, 0] = normal_x_data
                    normal_trajectory[:, 1] = normal_y_data

                    subjective_x_data = experiment["subjective"][strategy][boat_id]["x"]
                    subjective_y_data = experiment["subjective"][strategy][boat_id]["y"]
                    subjective_trajectory = np.zeros((len(subjective_x_data), 2))
                    subjective_trajectory[:, 0] = subjective_x_data
                    subjective_trajectory[:, 1] = subjective_y_data

                    if strategy not in experiment["normal_to_objective"]:
                        experiment["normal_to_objective"][strategy] = {}
                    experiment["normal_to_objective"][strategy][boat_id] = {}
                    # experiment["normal_to_objective"][strategy][boat_id]["pcm"] = sm.pcm(normal_trajectory,
                    #                                                                      objective_trajectory)
                    experiment["normal_to_objective"][strategy][boat_id]["frechet"] = sm.frechet_dist(normal_trajectory,
                                                                                                      objective_trajectory)

                    distance["nto"] = experiment["normal_to_objective"][strategy][boat_id]["frechet"]
                    # experiment["normal_to_objective"][strategy][boat_id]["area"] = sm.area_between_two_curves(
                    #     normal_trajectory,
                    #     objective_trajectory)
                    #
                    # experiment["normal_to_objective"][strategy][boat_id]["curve_length"] = sm.curve_length_measure(
                    #     normal_trajectory,
                    #     objective_trajectory)
                    #
                    # experiment["normal_to_objective"][strategy][boat_id]["dtw"], _ = sm.dtw(
                    #     normal_trajectory,
                    #     objective_trajectory)

                    if strategy not in experiment["normal_to_subjective"]:
                        experiment["normal_to_subjective"][strategy] = {}
                    experiment["normal_to_subjective"][strategy][boat_id] = {}

                    # experiment["normal_to_subjective"][strategy][boat_id]["pcm"] = sm.pcm(normal_trajectory,
                    #                                                                       subjective_trajectory)
                    experiment["normal_to_subjective"][strategy][boat_id]["frechet"] = sm.frechet_dist(
                        normal_trajectory,
                        subjective_trajectory)
                    distance["nts"] = experiment["normal_to_subjective"][strategy][boat_id]["frechet"]
                    # experiment["normal_to_subjective"][strategy][boat_id]["area"] = sm.area_between_two_curves(
                    #     normal_trajectory,
                    #     subjective_trajectory)
                    #
                    # experiment["normal_to_subjective"][strategy][boat_id]["curve_length"] = sm.curve_length_measure(
                    #     normal_trajectory,
                    #     subjective_trajectory)
                    #
                    # experiment["normal_to_subjective"][strategy][boat_id]["dtw"], _ = sm.dtw(
                    #     normal_trajectory,
                    #     subjective_trajectory)

                    if strategy not in experiment["subjective_to_objective"]:
                        experiment["subjective_to_objective"][strategy] = {}
                    experiment["subjective_to_objective"][strategy][boat_id] = {}

                    # experiment["subjective_to_objective"][strategy][boat_id]["pcm"] = sm.pcm(subjective_trajectory,
                    #                                                                          objective_trajectory)
                    experiment["subjective_to_objective"][strategy][boat_id]["frechet"] = sm.frechet_dist(
                        subjective_trajectory,
                        objective_trajectory)
                    distance["sto"] = experiment["subjective_to_objective"][strategy][boat_id]["frechet"]
                    # experiment["subjective_to_objective"][strategy][boat_id]["area"] = sm.area_between_two_curves(
                    #     subjective_trajectory,
                    #     objective_trajectory)
                    #
                    # experiment["subjective_to_objective"][strategy][boat_id]["curve_length"] = sm.curve_length_measure(
                    #     subjective_trajectory,
                    #     objective_trajectory)
                    #
                    # experiment["subjective_to_objective"][strategy][boat_id]["dtw"], _ = sm.dtw(
                    #     subjective_trajectory,
                    #     objective_trajectory)
                    distances.append(distance)
        df = pd.DataFrame(distances)
        df.to_csv('distances.csv')

    def get_stats(self, full_result):
        boat_ids = full_result["boats"].keys()
        raw_data = {}
        final_data = {}

        for boat_id in boat_ids:
            raw_data[boat_id] = {}
            raw_data[boat_id]["x"] = []
            raw_data[boat_id]["y"] = []
            raw_data[boat_id]["frame"] = []
            raw_data[boat_id]["yaw_rate"] = []
            raw_data[boat_id]["acc"] = []
            raw_data[boat_id]["jerk"] = []
            raw_data[boat_id]["lay"] = []
            raw_data[boat_id]["lat_jerk"] = []

            # Sparse trajectory according to sample rate.
            final_data[boat_id] = {}
            final_data[boat_id]["x"] = []
            final_data[boat_id]["y"] = []
            # Use these variables to compute derivatives.
            prev_acc = -1
            prev_lay = -1
            # FIXME: Skip first frames due to artificial spikes.
            start_frame = len(full_result["boats"][boat_id]) * 0.1
            end_frame = len(full_result["boats"][boat_id]) * 0.9

            for snapshot in full_result["boats"][boat_id]:
                frame = snapshot["frame"]
                if frame < start_frame or frame > end_frame:
                    continue

                x = snapshot["x"]
                y = snapshot["y"]
                lax = math.fabs(snapshot["lax"])
                lay = math.fabs(snapshot["lay"])
                acc = math.sqrt(lax ** 2 + lay ** 2)
                yaw_rate = math.fabs(snapshot["yaw_rate"])
                # if yaw_rate > 0.001:
                #     if frame < first_active_frame:
                #         first_active_frame = frame
                #     if frame > last_active_frame:
                #         last_active_frame = frame
                #
                #     if x < first_active_x:
                #         first_active_x = x
                #     if x > last_active_x:
                #         last_active_x = x

                dt = snapshot["dt"]
                # Compute derivatives of magnitude acceleration and lateral acceleration.
                if prev_acc == -1 or prev_lay == -1:
                    prev_acc = acc
                    prev_lay = lay

                jerk = math.fabs(acc - prev_acc) / dt
                lateral_jerk = math.fabs(lay - prev_lay) / dt
                prev_acc = acc
                prev_lay = lay

                if frame % self.trajectory_sample_rate == 0:
                    final_data[boat_id]["x"].append(x)
                    final_data[boat_id]["y"].append(y)

                # Save data for plotting.
                raw_data[boat_id]["x"].append(x)
                raw_data[boat_id]["y"].append(y)
                raw_data[boat_id]["frame"].append(frame)
                raw_data[boat_id]["yaw_rate"].append(yaw_rate)
                raw_data[boat_id]["acc"].append(acc / g)
                raw_data[boat_id]["jerk"].append(jerk / g)
                raw_data[boat_id]["lay"].append(lay / g)
                raw_data[boat_id]["lat_jerk"].append(lateral_jerk / g)
            # Add acc rate integral data by trapezoidal method.
            acc_data = np.array(raw_data[boat_id]["acc"])
            acc_area = np.trapz(acc_data)
            final_data[boat_id]["acc_area"] = acc_area

            jerk_data = np.array(raw_data[boat_id]["jerk"])
            jerk_area = np.trapz(jerk_data)
            final_data[boat_id]["jerk_area"] = jerk_area

            # Add lay rate integral data by trapezoidal method.
            lay_data = np.array(raw_data[boat_id]["lay"])
            lay_area = np.trapz(lay_data)
            final_data[boat_id]["lay_area"] = lay_area

            # Add lat_jerk rate integral data by trapezoidal method.
            lat_jerk_data = np.array(raw_data[boat_id]["lat_jerk"])
            lat_jerk_area = np.trapz(lat_jerk_data)
            final_data[boat_id]["lat_jerk_area"] = lat_jerk_area

            # Add yaw rate integral data by trapezoidal method.
            yaw_data = np.array(raw_data[boat_id]["yaw_rate"])
            yaw_area = np.trapz(yaw_data)
            final_data[boat_id]["yaw_area"] = yaw_area
        return final_data


class ResultsManager:
    def __init__(self, results_filename):
        results_data = None
        with open(results_filename) as file:
            results_data = json.load(file)
        self.results = results_data["boats"]
        self.y_limit = results_data["y_limit"]

    def plot_animations(self, ids):
        pass

    def plot_results(self, boat_ids=None, animated=False):
        if boat_ids is None:  # Plot all trajectories then.
            boat_ids = self.results.keys()
        if animated:
            self.plot_animations(boat_ids)
            return
        data = {}
        fig = plt.figure(figsize=(16, 20))
        trajectories_plot = fig.add_subplot(6, 1, 1)

        acc_plot = fig.add_subplot(6, 2, 3)
        agg_acc_plot = fig.add_subplot(6, 2, 4)

        lay_plot = fig.add_subplot(6, 2, 5)
        agg_lay_plot = fig.add_subplot(6, 2, 6)

        jerk_plot = fig.add_subplot(6, 2, 7)
        agg_jerk_plot = fig.add_subplot(6, 2, 8)

        lat_jerk_plot = fig.add_subplot(6, 2, 9)
        agg_lat_jerk_plot = fig.add_subplot(6, 2, 10)

        yaw_plot = fig.add_subplot(6, 2, 11)
        agg_yaw_plot = fig.add_subplot(6, 2, 12)

        trajectories_plot.set_ylim([0, self.y_limit * 2])
        mean_agg_acc = 0
        mean_agg_lay = 0
        mean_agg_jerk = 0
        mean_agg_lat_jerk = 0
        mean_agg_yaw = 0
        first_active_frame = 999999
        last_active_frame = -999999
        first_active_x = 999999
        last_active_x = -999999

        for boat_id in boat_ids:
            data[boat_id] = {}
            data[boat_id]["x"] = []
            data[boat_id]["y"] = []
            data[boat_id]["frame"] = []
            data[boat_id]["yaw_rate"] = []
            data[boat_id]["acc"] = []
            data[boat_id]["jerk"] = []
            data[boat_id]["lay"] = []
            data[boat_id]["lat_jerk"] = []
            # Use these variables to compute derivatives.
            prev_acc = -1
            prev_lay = -1
            # FIXME: Skip first frames due to artificial spikes.
            start_frame = len(self.results[boat_id]) * 0.1
            end_frame = len(self.results[boat_id]) * 0.9

            for snapshot in self.results[boat_id]:
                frame = snapshot["frame"]
                if frame < start_frame or frame > end_frame:
                    continue

                x = snapshot["x"]
                y = snapshot["y"]
                lax = math.fabs(snapshot["lax"])
                lay = math.fabs(snapshot["lay"])
                acc = math.sqrt(lax ** 2 + lay ** 2)
                yaw_rate = math.fabs(snapshot["yaw_rate"])
                if yaw_rate > 0.001:
                    if frame < first_active_frame:
                        first_active_frame = frame
                    if frame > last_active_frame:
                        last_active_frame = frame

                    if x < first_active_x:
                        first_active_x = x
                    if x > last_active_x:
                        last_active_x = x

                dt = snapshot["dt"]
                # Compute derivatives of magnitude acceleration and lateral acceleration.
                if prev_acc == -1 or prev_lay == -1:
                    prev_acc = acc
                    prev_lay = lay

                jerk = math.fabs(acc - prev_acc) / dt
                lateral_jerk = math.fabs(lay - prev_lay) / dt
                prev_acc = acc
                prev_lay = lay

                # Save data for plotting.
                data[boat_id]["x"].append(x)
                data[boat_id]["y"].append(y)
                data[boat_id]["frame"].append(frame)
                data[boat_id]["yaw_rate"].append(yaw_rate)
                data[boat_id]["acc"].append(acc / g)
                data[boat_id]["jerk"].append(jerk / g)
                data[boat_id]["lay"].append(lay / g)
                data[boat_id]["lat_jerk"].append(lateral_jerk / g)
            # Assign each id to a colour.
            current_colour = colours[int(boat_id) % len(colours)]

            # Overlay current boat trajectory
            trajectories_plot.plot(data[boat_id]["x"], data[boat_id]["y"], color=current_colour)

            # Add acc rate integral data by trapezoidal method.
            acc_data = np.array(data[boat_id]["acc"])
            acc_area = np.trapz(acc_data)
            bar = agg_acc_plot.bar(int(boat_id), height=acc_area, color=current_colour)
            agg_acc_plot.bar_label(bar, fmt='%.1f', padding=2)
            agg_acc_plot.set_ylabel('Integral of acceleration dt')
            # Rolling mean.
            mean_agg_acc = ((int(boat_id) * mean_agg_acc) + acc_area) / (int(boat_id) + 1)

            # Add jerk rate integral data by trapezoidal method.
            jerk_data = np.array(data[boat_id]["jerk"])
            jerk_area = np.trapz(jerk_data)
            bar = agg_jerk_plot.bar(int(boat_id), height=jerk_area, color=current_colour)
            agg_jerk_plot.bar_label(bar, fmt='%.1f', padding=2)
            agg_jerk_plot.set_ylabel('Integral of jerk dt')
            # Rolling mean.
            mean_agg_jerk = ((int(boat_id) * mean_agg_jerk) + jerk_area) / (int(boat_id) + 1)

            # Add lay rate integral data by trapezoidal method.
            lay_data = np.array(data[boat_id]["lay"])
            lay_area = np.trapz(lay_data)
            bar = agg_lay_plot.bar(int(boat_id), height=lay_area, color=current_colour)
            agg_lay_plot.bar_label(bar, fmt='%.1f', padding=2)
            agg_lay_plot.set_ylabel('Integral of lat. acceleration dt')
            # Rolling mean.
            mean_agg_lay = ((int(boat_id) * mean_agg_lay) + lay_area) / (int(boat_id) + 1)

            # Add lat_jerk rate integral data by trapezoidal method.
            lat_jerk_data = np.array(data[boat_id]["lat_jerk"])
            lat_jerk_area = np.trapz(lat_jerk_data)
            bar = agg_lat_jerk_plot.bar(int(boat_id), height=lat_jerk_area, color=current_colour)
            agg_lat_jerk_plot.bar_label(bar, fmt='%.1f', padding=2)
            agg_lat_jerk_plot.set_ylabel('Integral of lat. jerk dt')
            # Rolling mean.
            mean_agg_lat_jerk = ((int(boat_id) * mean_agg_lat_jerk) + lat_jerk_area) / (int(boat_id) + 1)

            # Add yaw rate integral data by trapezoidal method.
            yaw_data = np.array(data[boat_id]["yaw_rate"])
            yaw_area = np.trapz(yaw_data)
            bar = agg_yaw_plot.bar(int(boat_id), height=yaw_area, color=current_colour)
            agg_yaw_plot.bar_label(bar, fmt='%.1f', padding=2)
            agg_yaw_plot.set_ylabel('Integral of yaw rate dt')
            # Rolling mean.
            mean_agg_yaw = ((int(boat_id) * mean_agg_yaw) + yaw_area) / (int(boat_id) + 1)

            # Overlay current acceleration plot.
            acc_plot.plot(data[boat_id]["frame"], data[boat_id]["acc"], color=current_colour)

            # Overlay current jerk plot.
            jerk_plot.plot(data[boat_id]["frame"], data[boat_id]["jerk"], color=current_colour)

            # Overlay current lateral acceleration plot.
            # sample_freqs, spec_density = signal.periodogram(lay_data, fs=20, scaling='spectrum')

            # lay_plot.semilogy(sample_freqs, spec_density, color=current_colour)
            # lay_plot.set_ylim([1e-7, 1e3])
            # r = 2
            # rolling_lay = np.convolve(lay_data, np.ones(r), 'valid') / r
            # rolling_lay = np.hstack([rolling_lay, np.zeros(len(data[boat_id]["frame"]) - len(rolling_lay))])
            lay_plot.plot(data[boat_id]["frame"], data[boat_id]["lay"], color=current_colour)

            # Overlay current lateral jerk plot.
            lat_jerk_plot.plot(data[boat_id]["frame"], data[boat_id]["lat_jerk"], color=current_colour)

            # Overlay current yaw rate plot.
            yaw_plot.plot(data[boat_id]["frame"], data[boat_id]["yaw_rate"], color=current_colour)

        # Finalising aggregate yaw plot.
        bar = agg_yaw_plot.bar(len(boat_ids), height=mean_agg_yaw, hatch='/', linestyle='--', edgecolor='k')
        agg_yaw_plot.bar_label(bar, fmt='%.2f', padding=2)
        agg_yaw_plot.set_xticks([i for i in range(len(boat_ids) + 1)])
        agg_yaw_plot.set_xticklabels(list(boat_ids) + ["Mean"])

        # Finalising aggregate acc plot.
        bar = agg_acc_plot.bar(len(boat_ids), height=mean_agg_acc, hatch='/', linestyle='--', edgecolor='k')
        agg_acc_plot.bar_label(bar, fmt='%.2f', padding=2)
        agg_acc_plot.set_xticks([i for i in range(len(boat_ids) + 1)])
        agg_acc_plot.set_xticklabels(list(boat_ids) + ["Mean"])

        # Finalising aggregate jerk plot.
        bar = agg_jerk_plot.bar(len(boat_ids), height=mean_agg_jerk, hatch='/', linestyle='--', edgecolor='k')
        agg_jerk_plot.bar_label(bar, fmt='%.2f', padding=2)
        agg_jerk_plot.set_xticks([i for i in range(len(boat_ids) + 1)])
        agg_jerk_plot.set_xticklabels(list(boat_ids) + ["Mean"])

        # Finalising aggregate lay plot.
        bar = agg_lay_plot.bar(len(boat_ids), height=mean_agg_lay, hatch='/', linestyle='--', edgecolor='k')
        agg_lay_plot.bar_label(bar, fmt='%.2f', padding=2)
        agg_lay_plot.set_xticks([i for i in range(len(boat_ids) + 1)])
        agg_lay_plot.set_xticklabels(list(boat_ids) + ["Mean"])

        # Finalising aggregate lat_jerk plot.
        bar = agg_lat_jerk_plot.bar(len(boat_ids), height=mean_agg_lat_jerk, hatch='/', linestyle='--', edgecolor='k')
        agg_lat_jerk_plot.bar_label(bar, fmt='%.2f', padding=2)
        agg_lat_jerk_plot.set_xticks([i for i in range(len(boat_ids) + 1)])
        agg_lat_jerk_plot.set_xticklabels(list(boat_ids) + ["Mean"])

        # Write labels and plot details.
        acc_plot.set_xlabel('Simulation frame')
        acc_plot.set_ylabel("Acceleration (g)")
        acc_plot.set_xlim([first_active_frame, last_active_frame])
        acc_plot.set_ylim([0, 3])
        acc_plot.grid()

        jerk_plot.set_xlabel('Simulation frame')
        jerk_plot.set_ylabel('Jerk (g/s)')
        jerk_plot.set_xlim([first_active_frame, last_active_frame])
        jerk_plot.set_ylim([0, 30])
        jerk_plot.grid()

        lay_plot.set_xlabel('Simulation frame')
        lay_plot.set_ylabel('Lateral acceleration (g)')
        lay_plot.set_xlim([first_active_frame, last_active_frame])
        lay_plot.set_ylim([0, 3])
        lay_plot.grid()

        lat_jerk_plot.set_xlabel('Simulation frame')
        lat_jerk_plot.set_ylabel('Lateral jerk (g/s)')
        lat_jerk_plot.set_xlim([first_active_frame, last_active_frame])
        lat_jerk_plot.set_ylim([0, 10])
        lat_jerk_plot.grid()

        yaw_plot.set_xlabel('Simulation frame')
        yaw_plot.set_ylabel('Yaw rate (rad/s)')
        yaw_plot.set_xlim([first_active_frame, last_active_frame])
        yaw_plot.set_ylim([0, math.pi / 2])
        yaw_plot.grid()

        trajectories_plot.set_title('Trajectories')
        trajectories_plot.set_xlabel('X coordinate')
        trajectories_plot.set_ylabel('Y coordinate')
        # trajectories_plot.set_xlim([first_active_x, last_active_x])

        plt.tight_layout()
        plt.savefig('integral.pdf')

        plt.show()

results = MultiTrialResults(g=60)

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
