import math
import time
from utils import *
"""
Car physics model adapted from: https://github.com/spacejack/carphysics2d/blob/master/public/js/Car.js
Changes to make it more "boaty" are in order.
"""


class BoatModel:
    acquisition_threshold = 100
    def __init__(self, sim, boat_id, position = (0,0), boat_type="medium"):
        self.sim = sim
        self.boat_id = boat_id
        self.last_update = time.time()
        self.position = position
        self.goal = None
        self.goal_colour = 0
        self.distance_to_goal = 0
        self.boat_type = boat_type
        self.at_destination = False
        self.name = ""
        self.write_trajectories = False
        self.fixed_fps = True
        self.fps = 20.0
        self.frame_counter = 0
        # Do not run for more than 20 minutes.
        self.frame_limit = 24000
        self.avoiding = set()
        self.unfairly_avoided = set()

        self.init_kinematics()

    def get_position(self, zoom_factor=1):
        x = self.position[0] * zoom_factor
        y = self.position[1] * zoom_factor
        return x, y

    def get_goal(self, zoom_factor=1):
        x = self.goal[0] * zoom_factor
        y = self.goal[1] * zoom_factor
        return x, y

    def init_kinematics(self):
        #########
        # INPUT #
        #########
        self.left = 0
        self.right = 0
        self.throttle = 0
        self.brake = 0

        #########
        # STATS #
        #########
        self.heading = 0 #math.pi/2
        self.vx = 0  # X component of velocity in world coordinates (m/s)
        self.vy = 0  # Y component of velocity in world coordinates (m/s)
        self.lvx = 0  # X component of velocity in local coordinates (m/s)
        self.lvy = 0  # Y component of velocity in local coordinates (m/s)
        self.ax = 0  # X component of acceleration in world coordinates
        self.ay = 0  # Y component of acceleration in world coordinates
        self.lax = 0  # X component of acceleration in local coordinates
        self.lay = 0  # Y component of acceleration in local coordinates
        self.abs_velocity = 0  # Absolute velocity in m/s
        self.yaw_rate = 0  # Angular velocity in radians
        self.steering_input = 0.0  # Amount of steering input (-1.0 .. 1.0)
        self.steering_angle = 0.0  # Actual rudder angle (-maxSteer..maxSteer)
        self.gravity = 9.81  # m/s^2

        ########################
        #  VEHICLE PROPERTIES  #
        ########################

        if self.boat_type == "small":
            self.mass = 300  # kg
            self.inertiaScale = 1.0  # Multiply by mass for inertia
            self.halfWidth = 0.8  # Centre to side of chassis (metres)
            self.cgToFront = 2.0  # Centre of gravity to front of chassis (metres)
            self.cgToRear = 2.0  # Centre of gravity to rear of chassis
            self.cg_to_front_axle = 1.25  # Centre gravity to front axle
            self.cg_to_rear_axle = 1.25  # Centre gravity to rear axle
            self.cgHeight = 0.55  # Centre gravity height
            self.wheelRadius = 0.3  # Includes tire (also represents height of axle)
            self.wheelWidth = 0.2  # Used for render only
            self.tireGrip = 10000.0  # How much grip tires have
            self.lockGrip = 1  # % of grip available when wheel is locked
            self.engineForce = -1200.0
            self.brakeForce = 3000.0
            self.eBrakeForce = self.brakeForce / 2.5
            self.weightTransfer = 0.2  # How much weight is transferred during acceleration/braking
            self.maxSteer = math.pi / 1.5  # Maximum steering angle in radians
            self.cornerStiffnessFront = 5.0
            self.cornerStiffnessRear = 5.2
            self.water_resistance = 1  # air resistance (* vel)
            self.rollResist = 4.0  # rolling resistance force (* vel)
            self.max_speed = 30.0
        elif self.boat_type == "medium":
            self.mass = 1200  # kg
            self.inertiaScale = 1.0  # Multiply by mass for inertia
            self.halfWidth = 0.8  # Centre to side of chassis (metres)
            self.cgToFront = 2.0  # Centre of gravity to front of chassis (metres)
            self.cgToRear = 2.0  # Centre of gravity to rear of chassis
            self.cg_to_front_axle = 1.25  # Centre gravity to front axle
            self.cg_to_rear_axle = 1.25  # Centre gravity to rear axle
            self.cgHeight = 2.55  # Centre gravity height
            self.wheelRadius = 0.3  # Includes tire (also represents height of axle)
            self.wheelWidth = 0.2  # Used for render only
            self.tireGrip = 5000.0  # How much grip tires have
            self.lockGrip = 1  # % of grip available when wheel is locked
            self.engineForce = -2000.0
            self.brakeForce = 1000.0
            self.eBrakeForce = self.brakeForce / 2.5
            self.weightTransfer = 0.2  # How much weight is transferred during acceleration/braking
            self.maxSteer = math.pi / 4  # Maximum steering angle in radians
            self.cornerStiffnessFront = 5.0
            self.cornerStiffnessRear = 5.2
            self.water_resistance = 2.5  # air resistance (* vel)
            self.rollResist = 8.0  # rolling resistance force (* vel)
            self.max_speed = 20.0
        elif self.boat_type == "large":
            self.mass = 6000  # kg
            self.inertiaScale = 1.0  # Multiply by mass for inertia
            self.halfWidth = 0.8  # Centre to side of chassis (metres)
            self.cgToFront = 2.0  # Centre of gravity to front of chassis (metres)
            self.cgToRear = 2.0  # Centre of gravity to rear of chassis
            self.cg_to_front_axle = 1.25  # Centre gravity to front axle
            self.cg_to_rear_axle = 1.25  # Centre gravity to rear axle
            self.cgHeight = 5.55  # Centre gravity height
            self.wheelRadius = 0.3  # Includes tire (also represents height of axle)
            self.wheelWidth = 0.2  # Used for render only
            self.tireGrip = 1000.0  # How much grip tires have
            self.lockGrip = 1  # % of grip available when wheel is locked
            self.engineForce = -4000.0
            self.brakeForce = 3000.0
            self.eBrakeForce = self.brakeForce / 2.5
            self.weightTransfer = 0.2  # How much weight is transferred during acceleration/braking
            self.maxSteer = math.pi / 6  # Maximum steering angle in radians
            self.cornerStiffnessFront = 5.0
            self.cornerStiffnessRear = 5.2
            self.water_resistance = 5  # air resistance (* vel)
            self.rollResist = 1.0  # rolling resistance force (* vel)
            self.max_speed = 15.0

        self.inertia = self.mass * self.inertiaScale  # equals mass
        self.length = 2.5 #length
        self.axleWeightRatioFront = self.cg_to_rear_axle / self.length  # Percentage of vehicle weight on front
        self.axleWeightRatioRear = self.cg_to_front_axle / self.length  # Percentage of vehicle weight on rear

        ##############
        # DEBUG INFO #
        ##############

        self.DEBUG_desired_heading = 0
        self.DEBUG_relative_heading = 0
        self.DEBUG_message = ""

    def set_goal(self, x, y):
        self.goal = (x, y)

    def auto_drive_potential_field(self):
        if self.goal is None or self.at_destination:
            self.throttle = self.brake = self.left = self.right = 0.0
            return

        vx, vy = self.sim.get_velocity(self.position, self.boat_id)
        desired_heading = math.atan2(vy, vx)
        self.auto_steer(desired_heading)
        norm = math.sqrt(vx**2 + vy**2)
        self.auto_accelerate(norm)

        # FIXME: Workaround to avoid getting trapped in tangent.
        current_heading = (self.heading + (4*math.pi))
        relative_heading = (math.pi + current_heading - desired_heading) % (2*math.pi)
        tangent = math.tan(relative_heading)
        # Quickly turn to the other side to break away from tangent.
        # if self.distance_to_goal < 100 and math.fabs(tangent) > 1.0:
        #     self.left, self.right = 3*self.left, 3*self.right

        self.DEBUG_message = "tan:{:.1f}".format(tangent)
        self.DEBUG_relative_heading = relative_heading
        self.DEBUG_desired_heading = desired_heading


    def auto_steer(self, desired_heading):
        if self.goal is None:
            return

        gx, gy = self.goal
        cx, cy = self.position

        # desired_heading = math.atan2(gy - cy, gx - cx)
        current_heading = self.heading + math.pi
        current_heading %= 2*math.pi
        current_heading = (current_heading + math.pi) % (2*math.pi) - math.pi

        error = desired_heading - current_heading

        def adjust_error(error):
            if error < -math.pi:
                e = 2*math.pi + error
            elif error < math.pi:
                e = error
            else:
                e = error - 2*math.pi
            return e

        error = adjust_error(error)

        k_p = 5  # Proportional gain constant.
        if error < 0:
            self.right = bound(k_p * normalise(math.fabs(error), 0, 2*math.pi), 0, 1)
            self.left = 0.0
        else:
            self.right = 0.0
            self.left = bound(k_p * normalise(math.fabs(error), 0, 2*math.pi), 0, 1)

    def auto_accelerate(self, norm):
        if self.goal is None:
            return

        gx, gy = self.goal
        cx, cy = self.position

        # Distance is the error
        self.distance_to_goal = math.dist((gx, gy), (cx, cy))

        # Norm 1 == max speed. Decreases linearly.
        desired_speed = norm * self.max_speed
        # Positive: too slow. Negative: too fast.
        error = desired_speed - self.abs_velocity

        k_p = 1  # Proportional gain constant.
        if error > 0:
            self.throttle = bound(k_p * error, 0.0, 1.0)
            self.brake = 0
        else:
            self.throttle = 0
            self.brake = bound(k_p * -error, 0.0, 1.0)

    def reset_inputs(self):
        self.left = self.right = self.throttle = self.brake = 0.0

    def smooth_steering(self, steer_input, dt):
        steer = 0
        # Steering input present?
        if math.fabs(steer_input) > 0.001:
            # Move towards steering input
            steer = bound(steer + steer_input * dt * 2.0, -1.0, 1.0)
        else:  # No steering input
            if self.steering_input > 0:
                steer = max(self.steering_input - dt * 1.0, 0.0)
            elif self.steering_input < 0:
                steer = min(self.steering_input + dt * 1.0, 0.0)
        return steer

    def safe_steering(self, steer_input):
        abs_vel = min(self.abs_velocity, 250.0)
        steer = steer_input * (1.0 - (abs_vel / 280.0))
        return steer

    def simulate_kinematics(self):
        if self.at_destination:
            return

        self.frame_counter += 1

        # dt and fps calculation
        timestamp = time.time()
        dt = timestamp - self.last_update
        if dt == 0.0:
            dt = 0.01
        fps = 1.0 / dt
        # Ensure minimum fps
        if fps < 20:
            dt = 1.0 / 20.0

        if self.fixed_fps:
            dt = 1.0 / self.fps

        self.last_update = timestamp

        # Calculate steering and throttle input autonomously based on a potential field method.
        self.auto_drive_potential_field()

        # Process steering
        steer_input = self.right - self.left
        self.steering_input = self.smooth_steering(steer_input, dt)
        self.steering_input = self.safe_steering(self.steering_input)
        self.steering_angle = self.steering_input * self.maxSteer

        # Pre-calculate heading vector
        sin_hdg = math.sin(self.heading)
        cos_hdg = math.cos(self.heading)

        # Velocity in local car coordinates
        self.lvx = (cos_hdg * self.vx) + (sin_hdg * self.vy)
        self.lvy = (cos_hdg * self.vy) - (sin_hdg * self.vx)

        # Weight on axles based on centre of gravity and weight shift due to forward/reverse acceleration
        axle_weight_front = self.mass * (
                self.axleWeightRatioFront * self.gravity - self.weightTransfer * self.lax * self.cgHeight / self.length)

        axle_weight_rear = self.mass * (
                self.axleWeightRatioRear * self.gravity + self.weightTransfer * self.lax * self.cgHeight / self.length)

        # Resulting velocity of the wheels as result of the yaw rate of the car body.
        # v = yawrate * r where r is distance from axle to CG and yawRate (angular velocity) in rad/s.
        yaw_speed_front = self.cg_to_front_axle * self.yaw_rate
        yaw_speed_rear = -self.cg_to_rear_axle * self.yaw_rate

        # Calculate slip angles for front and rear wheels (a.k.a. alpha)
        slip_angle_front = math.atan2(self.lvy + yaw_speed_front, math.fabs(self.lvx)) - math.copysign(1,
                                                                                                   self.lvx) * self.steering_angle
        slip_angle_rear = math.atan2(self.lvy + yaw_speed_rear, math.fabs(self.lvx))

        tire_grip_front = self.tireGrip
        tire_grip_rear = self.tireGrip # * (1.0 * (1.0 - self.lockGrip))  # reduce rear grip when ebrake is on

        friction_force_front_cy = bound(-self.cornerStiffnessFront * slip_angle_front, -tire_grip_front,
                                      tire_grip_front) * axle_weight_front
        friction_force_rear_cy = bound(-self.cornerStiffnessRear * slip_angle_rear, -tire_grip_rear,
                                     tire_grip_rear) * axle_weight_rear

        #  Get amount of brake/throttle from our inputs
        brake = min(self.brake * self.brakeForce * self.eBrakeForce, self.brakeForce)
        throttle = self.throttle * self.engineForce

        #  Resulting force in local car coordinates.
        #  This is implemented as a RWD car only.
        traction_force_cx = throttle - brake * math.copysign(1, self.lvx)
        traction_force_cy = 0

        drag_force_cx = -self.rollResist * self.lvx - self.water_resistance * self.lvx * math.fabs(self.lvx)
        drag_force_cy = -self.rollResist * self.lvy - self.water_resistance * self.lvy * math.fabs(self.lvy)

        # total force in car coordinates
        total_force_cx = drag_force_cx + traction_force_cx
        total_force_cy = drag_force_cy + traction_force_cy + math.cos(
            self.steering_angle) * friction_force_front_cy + friction_force_rear_cy

        # acceleration along car axes
        self.lax = total_force_cx / self.mass  # forward/reverse accel
        self.lay = total_force_cy / self.mass  # sideways accel

        # acceleration in world coordinates
        self.ax = cos_hdg * self.lax - sin_hdg * self.lay
        self.ay = sin_hdg * self.lax + cos_hdg * self.lay

        # update velocity
        self.vx += self.ax * dt
        self.vy += self.ay * dt

        self.abs_velocity = math.sqrt(self.vx**2 + self.vy**2)
        # print("absolute velocity: {}".format(self.abs_velocity))
        # print("absolute acceleration: {}".format(math.sqrt(self.ax**2 + self.ay**2)))

        # calculate rotational forces
        angular_torque = (friction_force_front_cy + traction_force_cy) * self.cg_to_front_axle - friction_force_rear_cy * self.cg_to_rear_axle

        # If boat reaches goal at slow speed, consider mission complete.
        distance_to_goal = math.dist((self.position[0], self.position[1]), (self.goal[0], self.goal[1]))
        if (distance_to_goal < self.acquisition_threshold and self.abs_velocity < 10.0)\
                or self.frame_counter > self.frame_limit:
            self.at_destination = True
            self.sim.notify_finished_vehicle(self)

        #  Sim gets unstable at very slow speeds, so just stop the boat
        if (math.fabs(self.abs_velocity) < 0.5 and throttle == 0.0) or self.at_destination:
            angular_torque = self.yaw_rate = 0
            self.vx = self.vy = self.abs_velocity = 0

        angular_acceleration = angular_torque / self.inertia
        # Workaround to avoid jittery movement in beginning of simulation
        # angular_acceleration = bound(angular_acceleration, -1.0, 1.0)

        self.yaw_rate += angular_acceleration * dt
        # Workaround to avoid powerslides at low speeds.
        if math.fabs(self.abs_velocity < 1.0):
            self.yaw_rate = 0.0
        self.heading += self.yaw_rate * dt
        # self.heading %= 2*math.pi

        #  finally we can update position
        cx, cy = self.position
        cx += self.vx * dt
        cy += self.vy * dt
        self.position = (cx, cy)
        if self.write_trajectories:
            snapshot = {}
            # snapshot["boat_id"] = self.boat_id
            snapshot["timestamp"] = timestamp
            snapshot["frame"] = self.frame_counter
            snapshot["dt"] = dt
            snapshot["x"] = cx
            snapshot["y"] = cy
            # snapshot["velocity"] = self.abs_velocity
            snapshot["yaw_rate"] = self.yaw_rate
            snapshot["heading"] = math.degrees(self.heading)
            snapshot["angular_accel"] = angular_acceleration
            snapshot["lax"] = self.lax
            snapshot["lay"] = self.lay
            self.sim.trajectories[self.boat_id].append(snapshot)

    def relative_speed(self):
        return bound(self.abs_velocity / self.max_speed, 0.0, 1.0)
