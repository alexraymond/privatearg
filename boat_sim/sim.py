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

    def __init__(self, sim_config):
        # List of all BoatModels present.
        self.boats = []
        self.finished_boats = set()
        self.avoidance_min_distance = sim_config["avoidance_min_distance"]
        self.avoidance_max_distance = sim_config["avoidance_max_distance"]
        self.write_trajectories = sim_config["write_trajectories"]
        self.only_frontal_avoidance = True
        self.trajectories = {}
        self.sim_config = sim_config
        self.is_running = True
        # JSON (preferred) or CSV. Use lowercase.
        self.output_type = "json"
        self.results_filename = ""

    def concedes(self, id_a, id_b):
        """
        :return: True if vehicle with id_a concedes to id_b.
        """
        # print("{} > {}? {}".format(id_a, id_b, id_a < id_b))
        return id_a < id_b

    def notify_finished_vehicle(self, boat):
        self.finished_boats.add(boat)
        print("Boat {} reached target!".format(boat.boat_id))
        if len(self.finished_boats) == len(self.boats):
            self.is_running = False
            now = datetime.now()
            date_string = now.strftime("%d%b-%H%M")
            if self.output_type == "csv":
                filename = "results/result-{}-boats-{}.csv".format(len(self.boats), date_string)
                self.export_trajectories_csv(filename)
            elif self.output_type == "json":
                filename = "results/result-{}-boats-{}.json".format(len(self.boats), date_string)
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
        output_dict["boats"] = {}
        for boat in self.boats:
            boat_id = boat.boat_id
            output_dict["boats"][str(boat_id)] = self.trajectories[boat_id]
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
                df = bound(distance/max_speed_distance, 0.0, 1.0)
            v = np.array([df * np.cos(desired_heading), df * np.sin(desired_heading)])
            return v

        def velocity_for_avoidance(my_position, other_vehicle, min_distance, max_distance):
            tx, ty = other_vehicle.position
            mx, my = my_position

            if other_vehicle.at_destination:
                return np.zeros(2, dtype=np.float32)
            self.only_frontal_avoidance = True

            heading_from_obstacle = math.atan2(my - ty, mx - tx)
            heading_to_obstacle = math.atan2(ty - my, tx - mx)
            heading_to_obstacle = (heading_to_obstacle + (4*math.pi))
            their_heading = other_vehicle.heading
            relative_heading = (heading_to_obstacle - their_heading) % (2*math.pi)
            distance = math.dist((tx, ty), (mx, my))
            asymmetry = -math.pi/3
            k_d = 3.0
            # Avoid dividing by zero.
            if (max_distance == min_distance):
                df = 1
            else:
                df = (max_distance - distance) / (max_distance - min_distance)
            df = bound(k_d * df, 0.0, 2.0)

            # Special case: if behind, only consider min distance.
            if self.only_frontal_avoidance and math.pi / 2 < relative_heading < 3 * math.pi / 2:
                df = 0 if distance > min_distance else df
            else:  # Distance factor: 0 if distance > max, increases to 1 (where distance == min)
                df = 0 if distance > max_distance else df

            # Additional angle to force boats to choose starboard avoidance when head-on.
            if math.pi + math.pi > (relative_heading + math.pi) % (2*math.pi) > math.pi - math.pi/8:
                heading_from_obstacle = ((heading_from_obstacle + 2*math.pi) - asymmetry) % (2*math.pi)

            v = np.array([df * np.cos(heading_from_obstacle), df * np.sin(heading_from_obstacle)])
            return v

        v_goal = velocity_to_goal(position, goal)
        v = v_goal
        for vehicle in self.boats:
            their_id = vehicle.boat_id
            if their_id == vehicle_id:
                continue
            min_distance = self.avoidance_min_distance
            if self.concedes(vehicle_id, their_id):
                max_distance = min_distance + (vehicle.relative_speed() * self.avoidance_max_distance)
            else:
                max_distance = min_distance
            max_distance = bound(max_distance, min_distance, self.avoidance_max_distance)
            other_vehicle = self.boats[their_id]
            v += velocity_for_avoidance(position, other_vehicle, min_distance, max_distance)

        return v

    def load_boats(self, boats_dict):
        for boat_entry in boats_dict:
            boat = self.add_boat(self, boat_entry["start_x"], boat_entry["start_y"], boat_entry["size"])
            boat.set_goal(boat_entry["goal_x"], boat_entry["goal_y"])
            boat.name = boat_entry["name"]
            boat.heading = math.radians(boat_entry["initial_heading"])
            boat.goal_colour = boat_entry["colour"]
            boat.write_trajectories = self.write_trajectories

    def add_boat(self, sim, x, y, boat_type):
        boat_id = len(self.boats)
        boat = BoatModel(sim, boat_id, position=(x,y), boat_type=boat_type)
        if self.write_trajectories:
            self.trajectories[boat_id] = []
        self.boats.append(boat)
        return boat
