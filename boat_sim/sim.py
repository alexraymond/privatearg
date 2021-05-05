from vehicle_model import BoatModel
from utils import *
import numpy as np
import math
class Sim:
    """
    Main class for computing simulations and game logic in a headless manner.
    """

    def __init__(self):
        # List of all BoatModels present.
        self.vehicles = []

    def concedes(self, id_a, id_b):
        """
        :return: True if vehicle with id_a concedes to id_b.
        """
        # print("{} > {}? {}".format(id_a, id_b, id_a < id_b))
        return id_a < id_b

    def get_velocity(self, position, vehicle_id):
        v = np.zeros(2, dtype=np.float32)
        goal = self.vehicles[vehicle_id].goal

        def velocity_to_goal(position, goal):
            gx, gy = goal
            cx, cy = position
            # If distance is greater than that, vehicle should proceed at full speed.
            max_speed_distance = 100

            desired_heading = math.atan2(gy - cy, gx - cx)
            distance = math.dist((gx, gy), (cx, cy))

            # Distance factor: 1 if distance > max, decreases linearly.
            df = bound(distance/max_speed_distance, 0.0, 1.0)
            v = np.array([df * np.cos(desired_heading), df * np.sin(desired_heading)])
            return v

        def velocity_for_avoidance(my_position, their_position, min_distance, max_distance):
            tx, ty = their_position
            mx, my = my_position

            heading = math.atan2(my - ty, mx - tx)
            distance = math.dist((tx, ty), (mx, my))

            if distance == 0:
                distance = 0.01

            # # Special case: if behind, only consider min distance.
            # if heading > (math.pi - math.pi/2) and heading < (math.pi + math.pi/2):  # 135 to 225
            #     df = 0 if distance > min_distance else bound(min_distance / distance, 0.0, 1.5)

            # else: # Distance factor: 0 if distance > max, increases to 1 (where distance == min)
            df = 0 if distance > max_distance else bound(min_distance / distance, 0.0, 1.5)
            v = np.array([df * np.cos(heading), df * np.sin(heading)])
            return v

        v_goal = velocity_to_goal(position, goal)
        v = v_goal
        for vehicle in self.vehicles:
            their_id = vehicle.boat_id
            if their_id == vehicle_id:
                continue
            min_distance = 50
            max_distance = 500 if self.concedes(vehicle_id, their_id) else min_distance
            their_position = self.vehicles[their_id].position
            v += velocity_for_avoidance(position, their_position, min_distance, max_distance)

        return v

    def add_boat(self, sim, x, y, length):
        boat_id = len(self.vehicles)
        boat = BoatModel(sim, boat_id, position=(x,y), length=length)
        self.vehicles.append(boat)
        return boat
