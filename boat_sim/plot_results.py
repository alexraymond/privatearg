import json
import random
import sys
import os
import math
import numpy as np
import similaritymeasures as sm
import scipy.stats
from scipy import signal
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

colours = list("bgrcmyk") + list(mcolors.TABLEAU_COLORS.keys())
g = 9.81  # m/s^2


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

load_last = False

class MultiTrialResults:
    def __init__(self, g):
        self.results_folder = "results/"
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
            with open('final_results.json') as final_results_file:
                self.display_results = json.load(final_results_file)
        else:
            print("Calculating comparisons...")
            self.initialise()
            self.calculate_comparisons()
            self.pre_plot_results()
            with open('final_results.json', 'w') as final_results_file:
                json.dump(self.display_results, final_results_file, indent=4)

        self.plot_results()

    def initialise(self):
        sim_types = ["normal", "subjective", "objective"]
        # Important so we don't run out of memory. A value of 1 = sample one frame per data point.
        self.trajectory_sample_rate = 20
        for directory in self.directories:
            directory = directory.replace("results/", "")
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

        def add_data(plot, category, strategies):
            index = 0
            labels = []
            plot.set_title(category)
            short_names = {"ArgStrategy.RANDOM_CHOICE_PRIVATE": "random",
                           "ArgStrategy.LEAST_COST_PRIVATE": "least_cost",
                           "ArgStrategy.MOST_ATTACKS_PRIVATE": "most_attacks",
                           "ArgStrategy.LEAST_ATTACKERS_PRIVATE": "least_attackers"}
            data = []
            for strategy in strategies:
                labels.append(short_names[strategy])
                data.append(self.display_results[category][strategy])

            for i in range(len(data)):
                for j in range(i, len(data)):
                    mw_2s, p_mw_2s = scipy.stats.mannwhitneyu(data[i], data[j], alternative='two-sided')
                    if p_mw_2s < 0.05:
                        print("{}: MW two-sided {} vs {}. H = {}, p = {}".format(category, labels[i], labels[j], mw_2s, p_mw_2s))
                    mw_less, p_less = scipy.stats.mannwhitneyu(x=data[i], y=data[j], alternative='less')
                    if p_less < 0.05:
                        print("{}: MW less {} vs {}. U = {}, p = {}".format(category, labels[i], labels[j], mw_less, p_less))
                    mw_greater, p_greater = scipy.stats.mannwhitneyu(x=data[i], y=data[j], alternative='greater')
                    if p_greater < 0.05:
                        print("{}: MW greater {} vs {}. U = {}, p = {}".format(category, labels[i], labels[j], mw_greater, p_greater))

            plot.boxplot(data, positions=[0, 1, 2, 3], showfliers=False)
            plot.set_xticklabels(labels)

        ############################################################
        # Plotting kinematics figure.

        kinematics_fig = plt.figure(figsize=(20, 16))

        acc_plot = kinematics_fig.add_subplot(2, 3, 1)
        add_data(acc_plot, "acc_area", self.strategies)

        lay_plot = kinematics_fig.add_subplot(2, 3, 2)
        add_data(lay_plot, "lay_area", self.strategies)

        yaw_plot = kinematics_fig.add_subplot(2, 3, 3)
        add_data(yaw_plot, "yaw_area", self.strategies)

        jerk_plot = kinematics_fig.add_subplot(2, 3, 4)
        add_data(jerk_plot, "jerk_area", self.strategies)

        lat_jerk_plot = kinematics_fig.add_subplot(2, 3, 5)
        add_data(lat_jerk_plot, "lat_jerk_area", self.strategies)

        ############################################################
        # Plotting normal to objective figure.
        NTO_fig = plt.figure(figsize=(20, 16))

        NTO_pcm = NTO_fig.add_subplot(2, 3, 1)
        add_data(NTO_pcm, "NTO_pcm", self.strategies)

        NTO_frechet = NTO_fig.add_subplot(2, 3, 2)
        add_data(NTO_frechet, "NTO_frechet", self.strategies)

        NTO_area = NTO_fig.add_subplot(2, 3, 3)
        add_data(NTO_area, "NTO_area", self.strategies)

        NTO_curve = NTO_fig.add_subplot(2, 3, 4)
        add_data(NTO_curve, "NTO_curve_length", self.strategies)

        NTO_dtw = NTO_fig.add_subplot(2, 3, 5)
        add_data(NTO_dtw, "NTO_dtw", self.strategies)

        ############################################################
        # Plotting normal to subjective figure.
        NTS_fig = plt.figure(3, figsize=(20, 16))
        NTS_pcm = NTS_fig.add_subplot(2, 3, 1)
        add_data(NTS_pcm, "NTS_pcm", self.strategies)

        NTS_frechet = NTS_fig.add_subplot(2, 3, 2)
        add_data(NTS_frechet, "NTS_frechet", self.strategies)

        NTS_area = NTS_fig.add_subplot(2, 3, 3)
        add_data(NTS_area, "NTS_area", self.strategies)

        NTS_curve = NTS_fig.add_subplot(2, 3, 4)
        add_data(NTS_curve, "NTS_curve_length", self.strategies)

        NTS_dtw = NTS_fig.add_subplot(2, 3, 5)
        add_data(NTS_dtw, "NTS_dtw", self.strategies)

        ############################################################
        # Plotting subjective to objective figure.
        STO_fig = plt.figure(4, figsize=(20, 16))
        STO_pcm = STO_fig.add_subplot(2, 3, 1)
        add_data(STO_pcm, "STO_pcm", self.strategies)

        STO_frechet = STO_fig.add_subplot(2, 3, 2)
        add_data(STO_frechet, "STO_frechet", self.strategies)

        STO_area = STO_fig.add_subplot(2, 3, 3)
        add_data(STO_area, "STO_area", self.strategies)

        STO_curve = STO_fig.add_subplot(2, 3, 4)
        add_data(STO_curve, "STO_curve_length", self.strategies)

        STO_dtw = STO_fig.add_subplot(2, 3, 5)
        add_data(STO_dtw, "STO_dtw", self.strategies)

        ############################################################
        # Plotting.

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

                        self.display_results["NTO_pcm"][strategy].append(
                            experiment["normal_to_objective"][strategy][boat_id]["pcm"])
                        self.display_results["NTO_frechet"][strategy].append(
                            experiment["normal_to_objective"][strategy][boat_id]["frechet"])
                        self.display_results["NTO_area"][strategy].append(
                            experiment["normal_to_objective"][strategy][boat_id]["area"])
                        self.display_results["NTO_curve_length"][strategy].append(
                            experiment["normal_to_objective"][strategy][boat_id]["curve_length"])
                        self.display_results["NTO_dtw"][strategy].append(
                            experiment["normal_to_objective"][strategy][boat_id]["dtw"])

                        self.display_results["NTS_pcm"][strategy].append(
                            experiment["normal_to_subjective"][strategy][boat_id]["pcm"])
                        self.display_results["NTS_frechet"][strategy].append(
                            experiment["normal_to_subjective"][strategy][boat_id]["frechet"])
                        self.display_results["NTS_area"][strategy].append(
                            experiment["normal_to_subjective"][strategy][boat_id]["area"])
                        self.display_results["NTS_curve_length"][strategy].append(
                            experiment["normal_to_subjective"][strategy][boat_id]["curve_length"])
                        self.display_results["NTS_dtw"][strategy].append(
                            experiment["normal_to_subjective"][strategy][boat_id]["dtw"])

                        self.display_results["STO_pcm"][strategy].append(
                            experiment["subjective_to_objective"][strategy][boat_id]["pcm"])
                        self.display_results["STO_frechet"][strategy].append(
                            experiment["subjective_to_objective"][strategy][boat_id]["frechet"])
                        self.display_results["STO_area"][strategy].append(
                            experiment["subjective_to_objective"][strategy][boat_id]["area"])
                        self.display_results["STO_curve_length"][strategy].append(
                            experiment["subjective_to_objective"][strategy][boat_id]["curve_length"])
                        self.display_results["STO_dtw"][strategy].append(
                            experiment["subjective_to_objective"][strategy][boat_id]["dtw"])

    def calculate_comparisons(self):
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
                    experiment["normal_to_objective"][strategy][boat_id]["pcm"] = sm.pcm(normal_trajectory,
                                                                                         objective_trajectory)
                    experiment["normal_to_objective"][strategy][boat_id]["frechet"] = sm.frechet_dist(normal_trajectory,
                                                                                                      objective_trajectory)
                    experiment["normal_to_objective"][strategy][boat_id]["area"] = sm.area_between_two_curves(
                        normal_trajectory,
                        objective_trajectory)

                    experiment["normal_to_objective"][strategy][boat_id]["curve_length"] = sm.curve_length_measure(
                        normal_trajectory,
                        objective_trajectory)

                    experiment["normal_to_objective"][strategy][boat_id]["dtw"], _ = sm.dtw(
                        normal_trajectory,
                        objective_trajectory)

                    if strategy not in experiment["normal_to_subjective"]:
                        experiment["normal_to_subjective"][strategy] = {}
                    experiment["normal_to_subjective"][strategy][boat_id] = {}

                    experiment["normal_to_subjective"][strategy][boat_id]["pcm"] = sm.pcm(normal_trajectory,
                                                                                          subjective_trajectory)
                    experiment["normal_to_subjective"][strategy][boat_id]["frechet"] = sm.frechet_dist(
                        normal_trajectory,
                        subjective_trajectory)
                    experiment["normal_to_subjective"][strategy][boat_id]["area"] = sm.area_between_two_curves(
                        normal_trajectory,
                        subjective_trajectory)

                    experiment["normal_to_subjective"][strategy][boat_id]["curve_length"] = sm.curve_length_measure(
                        normal_trajectory,
                        subjective_trajectory)

                    experiment["normal_to_subjective"][strategy][boat_id]["dtw"], _ = sm.dtw(
                        normal_trajectory,
                        subjective_trajectory)

                    if strategy not in experiment["subjective_to_objective"]:
                        experiment["subjective_to_objective"][strategy] = {}
                    experiment["subjective_to_objective"][strategy][boat_id] = {}

                    experiment["subjective_to_objective"][strategy][boat_id]["pcm"] = sm.pcm(subjective_trajectory,
                                                                                             objective_trajectory)
                    experiment["subjective_to_objective"][strategy][boat_id]["frechet"] = sm.frechet_dist(
                        subjective_trajectory,
                        objective_trajectory)
                    experiment["subjective_to_objective"][strategy][boat_id]["area"] = sm.area_between_two_curves(
                        subjective_trajectory,
                        objective_trajectory)

                    experiment["subjective_to_objective"][strategy][boat_id]["curve_length"] = sm.curve_length_measure(
                        subjective_trajectory,
                        objective_trajectory)

                    experiment["subjective_to_objective"][strategy][boat_id]["dtw"], _ = sm.dtw(
                        subjective_trajectory,
                        objective_trajectory)

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

        plt.show()

# results = MultiTrialResults(g=30)

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
