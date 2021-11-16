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

    def __init__(self, sim_config, results_path=None, dialogue_data=None, subjective=False, objective=False,
                 budget=1000, strategy=None, avoiding_losers=True):
        """
        Initialises the headless Sim. We load the sim config and the pre-processed dialogue data.
        The sim executes the trajectories of all boats and records them in fine detail on a results file,
        which will be processed later to analyse the dynamics of the agents.
        :param sim_config: The sim config dict, extracted from the general config JSON file.
        :param results_path: The output path to write the results file for this simulation.
        :param dialogue_data: The dict containing the pre-processed dialogue data.
        :param subjective: Whether we are running a subjective trajectory.
        :param objective: Whether we are running an objective trajectory.
        :param budget: The privacy budget allocated to each agent.
        :param strategy: The current dialogue strategy used in the dialogue data.
        :param avoiding_losers: If a loser vehicle fails to get out of the way, should
        the winner also avoid them anyway? True if yes.
        """
        # List of all BoatModels present.
        self.boats = []
        self.finished_boats = set()

        # Minimum and maximum distance of the avoidance cases.
        # Max distance is when the dialogue begins, and min is where it must end.
        self.avoidance_min_distance = sim_config["avoidance_min_distance"]
        self.avoidance_max_distance = sim_config["avoidance_max_distance"]
        self.write_trajectories = sim_config["write_trajectories"]
        self.subjective_trajectories = subjective
        self.objective_trajectories = objective

        # The agent will never avoid a loser in the subjective case.
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
            if self.all_dialogue_data is not None:
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
        """
        Captures winners and subjective unfairness instances in the dialogue data.
        Note: this ignores the privacy budget and returns the ground truth results.
        """
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
        """
        Processes the dialogue results according to the privacy budget.
        """
        # FIXME: Added this to simulate old scenarios without dialogues. (Legacy)
        if self.all_dialogue_data is None:
            for a in range(0, 16):
                for b in range(0, 16):
                    self.costs[(a, b)] = 0
                    self.subjectively_unfair[(a, b)] = False
                    self.winners[(a, b)] = a if a > b else b
            return

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
        a, b = sorted([id_a, id_b])
        return self.winners[(a, b)] == id_b

    def notify_finished_vehicle(self, boat):
        """
        Callback from the simulation every time a boat reaches its destination.
        :param boat: Finished boat.
        """
        self.finished_boats.add(boat)
        # print("Boat {} reached target!".format(boat.boat_id))

        # When all boats are finished, we can save the trajectories.
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
        """
        Saves the trajectories in CSV format.
        :param filename: Output file.
        """
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
        """
        Saves the trajectories in JSON format.
        :param filename: Output file.
        """
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
        """
        This is the central mechanism for the potential field method.
        In this simple method of collision avoidance, we compute forces from vectors emitted by
        neighbouring agents, and compute the sum of those to form a velocity vector that escapes
        the agents and drives in a specific direction, whilst heading towards the goal.
        This (intended) velocity vector will govern acceleration and steering input.
        :param position: The x,y position in space where we need a velocity vector.
        :param vehicle_id: The id of the vehicle associated with this velocity.
        :return: A 2D np.array with the velocity vector.
        """
        v = np.zeros(2, dtype=np.float32)
        goal = self.boats[vehicle_id].goal

        def velocity_to_goal(position, goal):
            """
            Helper function. The first component of the potential field method is a direct
            velocity to the goal. This is simply calculated using trigonometry and capped
            at a specific maximum speed.
            :param position: Position of the agent.
            :param goal: Position of the goal.
            :return: A 2D np.array with the velocity vector.
            """
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
            """
            This is the second component. We now compute a vector that tries to avoid another agent.
            :param my_vehicle: Boat object of the agent.
            :param their_vehicle: Boat object of the other agent.
            :param min_distance: Minimum avoidance distance.
            :param max_distance: Maximum avoidance distance.
            :return: A 2D np.array with the velocity vector.
            """
            tx, ty = their_vehicle.position
            mx, my = my_vehicle.position
            zero_v = np.zeros(2, dtype=np.float32)
            my_id = my_vehicle.boat_id
            their_id = their_vehicle.boat_id

            # Check who wins the dialogue.
            i_lost = self.concedes(my_id, their_id)
            i_won = not i_lost
            a, b = sorted([my_id, their_id])
            max_budget = self.max_budget

            # Finds a proportional dialogue cost according to the budget, in [0,1].
            proportional_cost = self.costs[(a, b)] / max_budget if max_budget > 0 else 1

            # Calculates the proportional activation distance according to the proportional cost.
            activation_distance = bound(max_distance - (proportional_cost * max_distance), min_distance, max_distance)

            # Ignore vehicles that have already arrived.
            if their_vehicle.at_destination:
                return zero_v

            # This variable controls whether we want vehicles to ignore rear avoidance.
            # This can be particularly helpful when two vehicles are following each other.
            self.only_frontal_avoidance = True

            heading_from_obstacle = math.atan2(my - ty, mx - tx)
            heading_to_obstacle = math.atan2(ty - my, tx - mx)
            heading_to_obstacle = (heading_to_obstacle + (4 * math.pi))
            their_heading = their_vehicle.heading
            relative_heading = (heading_to_obstacle - their_heading) % (2 * math.pi)
            distance = math.dist((tx, ty), (mx, my))
            asymmetry = -math.pi / 3
            # Some adjustments to a proportional controller.
            k_d = 2.0
            # p = {1.0, 2.0, 3.0} mean linear, quadratic, and cubic decay, respectively.
            p = 2
            max_df = 1.5

            # First time the potential field is activated.
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
        """
        Load the boats from the boats dict.
        :param boats_dict: Dictionary containing boat information, loaded from config.
        """
        for boat_entry in boats_dict:
            boat = self.add_boat(self, boat_entry["id"], boat_entry["start_x"], boat_entry["start_y"],
                                 boat_entry["size"])
            boat.set_goal(boat_entry["goal_x"], boat_entry["goal_y"])
            boat.name = boat_entry["name"]
            boat.heading = math.radians(boat_entry["initial_heading"])
            boat.goal_colour = boat_entry["colour"]
            boat.write_trajectories = self.write_trajectories

    def add_boat(self, sim, boat_id, x, y, boat_type):
        """
        Constructs a BoatModel object and adds it to the simulation.
        :param sim: Simulation handle.
        :param boat_id: Boat ID.
        :param x: X coordinate.
        :param y: Y coordinate.
        :param boat_type: Type of boat: {'small', 'medium', 'large'}
        :return: The created BoatModel reference.
        """
        boat = BoatModel(sim=sim, boat_id=boat_id, position=(x, y), boat_type=boat_type)
        if self.write_trajectories:
            self.trajectories[boat_id] = []
        self.boats.append(boat)
        return boat
