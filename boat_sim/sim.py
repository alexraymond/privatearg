from vehicle_model import BoatModel
from utils import *
import numpy as np
import math
import csv
import json
from datetime import datetime


class Sim:
    """
    Main class for computing simulations and game logic in a headless manner.
    """

    def __init__(self, sim_config, results_path, dialogue_data, subjective=False, objective=False,
                 budget=None, strategy=None, avoiding_losers=True):
        # List of all BoatModels present.
        self.boats = []
        self.finished_boats = set()
        self.avoidance_min_distance = sim_config["avoidance_min_distance"]
        self.avoidance_max_distance = sim_config["avoidance_max_distance"]
        self.write_trajectories = sim_config["write_trajectories"]
        self.subjective_trajectories = subjective
        self.objective_trajectories = objective
        if subjective:
            avoiding_losers = False
        self.all_dialogue_data = dialogue_data
        self.only_frontal_avoidance = True
        self.max_budget = 2 * budget  # The budget received is individual. Communication cost includes both.
        self.strategy = strategy
        self.winners = {}
        self.costs = {}
        self.subjectively_unfair = {}
        self.trajectories = {}
        # FIXME: Stupid JSON nesting.
        if not objective:
            self.specific_dialogue_results = self.all_dialogue_data['dialogue_results'][strategy][str(budget)]["agents"]
            self.process_dialogues()
        else:
            self.specific_dialogue_results = self.all_dialogue_data['ground_truth']
            self.process_ground_truth()
        self.avoiding_losers = avoiding_losers
        self.results_path = results_path
        self.sim_config = sim_config
        self.is_running = True
        # JSON (preferred) or CSV. Use lowercase.
        self.output_type = "json"
        self.results_filename = ""

    def process_ground_truth(self):
        for result in self.specific_dialogue_results.keys():
            agents_str = result
            agents_str = agents_str.replace("(", "")
            agents_str = agents_str.replace(")", "")
            agents_str = agents_str.split(", ")
            defender = int(agents_str[0])
            challenger = int(agents_str[1])
            winner = self.specific_dialogue_results[result]
            a, b = sorted([defender, challenger])
            if (a, b) not in self.winners:
                self.winners[(a, b)] = winner
                self.costs[(a, b)] = 0
            if (defender, challenger) not in self.subjectively_unfair:
                self.subjectively_unfair[(defender, challenger)] = False

    def process_dialogues(self):
        for agent in self.specific_dialogue_results.values():
            for result in agent["dialogue_results"].keys():
                agents_str = result
                agents_str = agents_str.replace("(", "")
                agents_str = agents_str.replace(")", "")
                agents_str = agents_str.split(", ")
                defender = int(agents_str[0])
                challenger = int(agents_str[1])
                winner = agent["dialogue_results"][result]["winner"]
                total_cost = agent["dialogue_results"][result]["total_privacy_cost"]
                unfair = agent["dialogue_results"][result]["considered_unfair"]
                a, b = sorted([defender, challenger])
                if (a, b) not in self.winners:
                    self.winners[(a, b)] = winner
                    self.costs[(a, b)] = total_cost
                if (defender, challenger) not in self.subjectively_unfair:
                    self.subjectively_unfair[(defender, challenger)] = unfair

    def concedes(self, id_a, id_b):
        """
        :return: True if vehicle with id_a concedes to id_b.
        """
        # print("{} > {}? {}".format(id_a, id_b, id_a < id_b))
        a, b = sorted([id_a, id_b])
        return self.winners[(a, b)] == id_b

    def notify_finished_vehicle(self, boat):
        self.finished_boats.add(boat)
        # print("Boat {} reached target!".format(boat.boat_id))
        if len(self.finished_boats) == len(self.boats):
            self.is_running = False
            if self.output_type == "csv":
                filename = "results/result-{}-boats.csv".format(len(self.boats))
                self.export_trajectories_csv(filename)
            elif self.output_type == "json":
                if self.objective_trajectories:
                    sim_type = "objective"
                    filename = self.results_path + "/{}-g-{}-{}-boats.json".format(sim_type, self.max_budget,
                                                                                   len(self.boats))
                elif self.subjective_trajectories:
                    sim_type = "subjective"
                    filename = self.results_path + "/{}-{}-g-{}-{}-boats.json".format(sim_type, self.strategy,
                                                                                      self.max_budget,
                                                                                      len(self.boats))
                else:
                    sim_type = "normal"
                    filename = self.results_path + "/{}-{}-g-{}-{}-boats.json".format(sim_type, self.strategy,
                                                                                      self.max_budget,
                                                                                      len(self.boats))
                self.export_trajectories_json(filename)
                self.results_filename = filename

    def export_trajectories_csv(self, filename):
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            # Get any snapshot and use the keys as headers.
            headers = self.trajectories[0][0].keys()
            writer.writerow(headers)
            for boat in self.boats:
                boat_id = boat.boat_id
                for snapshot in self.trajectories[boat_id]:
                    row = []
                    for key in snapshot.keys():
                        row.append(snapshot[key])
                    writer.writerow(row)
            file.close()

    def export_trajectories_json(self, filename):
        output_dict = {}
        output_dict["y_limit"] = self.sim_config["graphics"]["height"]
        output_dict["avoidances"] = {}
        output_dict["emergency_avoidances"] = {}
        output_dict["boats"] = {}
        for boat in self.boats:
            boat_id = boat.boat_id
            output_dict["boats"][str(boat_id)] = self.trajectories[boat_id]
            output_dict["emergency_avoidances"][str(boat_id)] = list(boat.unfairly_avoided)
            output_dict["avoidances"][str(boat_id)] = list(boat.avoiding)
        with open(filename, 'w') as file:
            json.dump(output_dict, file, indent=1)
            file.close()

    def get_velocity(self, position, vehicle_id):
        v = np.zeros(2, dtype=np.float32)
        goal = self.boats[vehicle_id].goal

        def velocity_to_goal(position, goal):
            gx, gy = goal
            cx, cy = position
            # If distance is greater than that, vehicle should proceed at full speed.
            max_speed_distance = 200

            desired_heading = math.atan2(gy - cy, gx - cx)
            distance = math.dist((gx, gy), (cx, cy))

            # Distance factor: 1 if distance > max, decreases linearly.
            if distance > max_speed_distance:
                df = 1
            else:
                df = bound(distance / max_speed_distance, 0.0, 1.0)
            v = np.array([df * np.cos(desired_heading), df * np.sin(desired_heading)])
            return v

        def velocity_for_avoidance(my_vehicle, their_vehicle, min_distance, max_distance):
            tx, ty = their_vehicle.position
            mx, my = my_vehicle.position
            zero_v = np.zeros(2, dtype=np.float32)
            my_id = my_vehicle.boat_id
            their_id = their_vehicle.boat_id
            i_lost = self.concedes(my_id, their_id)
            i_won = not i_lost
            a, b = sorted([my_id, their_id])
            max_budget = self.max_budget
            proportional_cost = self.costs[(a, b)] / max_budget if max_budget > 0 else 1
            activation_distance = bound(max_distance - (proportional_cost * max_distance), min_distance, max_distance)

            if their_vehicle.at_destination:
                return zero_v
            self.only_frontal_avoidance = True

            heading_from_obstacle = math.atan2(my - ty, mx - tx)
            heading_to_obstacle = math.atan2(ty - my, tx - mx)
            heading_to_obstacle = (heading_to_obstacle + (4 * math.pi))
            their_heading = their_vehicle.heading
            relative_heading = (heading_to_obstacle - their_heading) % (2 * math.pi)
            distance = math.dist((tx, ty), (mx, my))
            asymmetry = -math.pi / 3
            k_d = 1.0
            # p = {1.0, 2.0, 3.0} mean linear, quadratic, and cubic decay, respectively.
            p = 1
            max_df = 1.0

            # First time the potential field is activated
            if i_lost and distance < activation_distance and their_id not in my_vehicle.avoiding:
                if not self.subjectively_unfair[(my_id, their_id)]:
                    my_vehicle.avoiding.add(their_id)

            # Avoid dividing by zero.
            if i_won and distance < min_distance and self.avoiding_losers:
                df = max_df
            elif i_lost and distance < min_distance and not self.subjective_trajectories:
                df = max_df
            elif distance > max_distance:
                df = 0
            elif i_lost and their_id in my_vehicle.avoiding:
                df = k_d * math.pow((max_distance - distance), p) / math.pow((max_distance - min_distance), p)
            else:
                df = 0

            df = bound(df, 0.0, max_df)

            # Special case: if behind, only consider min distance.
            if self.only_frontal_avoidance and math.pi / 2 < relative_heading < 3 * math.pi / 2:
                df = 0 if distance > min_distance else df
            else:  # Distance factor: 0 if distance > max, increases to 1 (where distance == min)
                df = 0 if distance > max_distance else df

            # Additional angle to force boats to choose starboard avoidance when head-on.
            if math.pi + math.pi > (relative_heading + math.pi) % (2 * math.pi) > math.pi - math.pi / 8:
                heading_from_obstacle = ((heading_from_obstacle + 2 * math.pi) - asymmetry) % (2 * math.pi)

            v = np.array([df * np.cos(heading_from_obstacle), df * np.sin(heading_from_obstacle)])

            # Add this vehicle to the set of vehicles you had to wrongfully avoid if you were affected by its field.
            if i_won and not np.array_equal(v, zero_v):
                my_vehicle.unfairly_avoided.add(their_id)
            return v

        v_goal = velocity_to_goal(position, goal)
        v = v_goal
        for vehicle in self.boats:
            their_id = vehicle.boat_id
            if their_id == vehicle_id:
                continue
            min_distance = self.avoidance_min_distance
            # # Done so that slow vehicles don't need to worry about faster boats in the distance.
            # if self.concedes(vehicle_id, their_id):
            #     max_distance = min_distance + (vehicle.relative_speed() * self.avoidance_max_distance)
            # else:
            #     max_distance = self.avoidance_max_distance
            max_distance = self.avoidance_max_distance
            max_distance = bound(max_distance, min_distance, self.avoidance_max_distance)
            my_vehicle = self.boats[vehicle_id]
            other_vehicle = self.boats[their_id]
            v += velocity_for_avoidance(my_vehicle, other_vehicle, min_distance, max_distance)
        return v

    def load_boats(self, boats_dict):
        for boat_entry in boats_dict:
            boat = self.add_boat(self, boat_entry["id"], boat_entry["start_x"], boat_entry["start_y"],
                                 boat_entry["size"])
            boat.set_goal(boat_entry["goal_x"], boat_entry["goal_y"])
            boat.name = boat_entry["name"]
            boat.heading = math.radians(boat_entry["initial_heading"])
            boat.goal_colour = boat_entry["colour"]
            boat.write_trajectories = self.write_trajectories

    def add_boat(self, sim, boat_id, x, y, boat_type):
        boat = BoatModel(sim=sim, boat_id=boat_id, position=(x, y), boat_type=boat_type)
        if self.write_trajectories:
            self.trajectories[boat_id] = []
        self.boats.append(boat)
        return boat
