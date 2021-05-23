import json
import random
import sys
import math
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

colours = list("bgrcmyk") + list(mcolors.TABLEAU_COLORS.keys())
g = 9.81 #m/s^2

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

        acc_plot          = fig.add_subplot(6, 2, 3)
        agg_acc_plot      = fig.add_subplot(6, 2, 4)

        lay_plot          = fig.add_subplot(6, 2, 5)
        agg_lay_plot      = fig.add_subplot(6, 2, 6)

        jerk_plot         = fig.add_subplot(6, 2, 7)
        agg_jerk_plot     = fig.add_subplot(6, 2, 8)

        lat_jerk_plot     = fig.add_subplot(6, 2, 9)
        agg_lat_jerk_plot = fig.add_subplot(6, 2, 10)

        yaw_plot          = fig.add_subplot(6, 2, 11)
        agg_yaw_plot      = fig.add_subplot(6, 2, 12)

        trajectories_plot.set_ylim([0, self.y_limit*2])
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
                acc = math.sqrt(lax**2 + lay**2)
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
        yaw_plot.set_ylim([0, math.pi/2])
        yaw_plot.grid()
        
        trajectories_plot.set_title('Trajectories')
        trajectories_plot.set_xlabel('X coordinate')
        trajectories_plot.set_ylabel('Y coordinate')
        # trajectories_plot.set_xlim([first_active_x, last_active_x])

        plt.tight_layout()

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
