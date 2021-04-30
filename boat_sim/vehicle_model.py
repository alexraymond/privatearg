import math
import time

"""
Car physics model adapted from: https://github.com/spacejack/carphysics2d/blob/master/public/js/Car.js
Made changes to make it more "boaty" are in order.
"""


def bound(value, low, high):
    return max(low, min(high, value))

def normalise(value, min_v, max_v):
    return (value - min_v) / (max_v - min_v)


class BoatModel:
    def __init__(self, center_x=0, center_y=0, length=0):
        self.last_update = time.time()
        self.init_kinematics()
        self.cx = center_x
        self.cy = center_y
        self.goal_x = None
        self.goal_y = None

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

        ########################
        #  VEHICLE PROPERTIES  #
        ########################

        self.gravity = 9.81  # m/s^2
        self.mass = 1200  # kg
        self.inertiaScale = 1.0  # Multiply by mass for inertia
        self.halfWidth = 0.8  # Centre to side of chassis (metres)
        self.cgToFront = 2.0  # Centre of gravity to front of chassis (metres)
        self.cgToRear = 2.0  # Centre of gravity to rear of chassis
        self.cgToFrontAxle = 1.25  # Centre gravity to front axle
        self.cgToRearAxle = 1.25  # Centre gravity to rear axle
        self.cgHeight = 0.55  # Centre gravity height
        self.wheelRadius = 0.3  # Includes tire (also represents height of axle)
        self.wheelWidth = 0.2  # Used for render only
        self.tireGrip = 100.0  # How much grip tires have
        self.lockGrip = 1  # % of grip available when wheel is locked
        self.engineForce = -8000.0
        self.brakeForce = 12000.0
        self.eBrakeForce = self.brakeForce / 2.5
        self.weightTransfer = 0.2  # How much weight is transferred during acceleration/braking
        self.maxSteer = math.pi/2  # Maximum steering angle in radians
        self.cornerStiffnessFront = 5.0
        self.cornerStiffnessRear = 5.2
        self.airResist = 2.5  # air resistance (* vel)
        self.rollResist = 8.0  # rolling resistance force (* vel)
        self.max_speed = 40.0

        self.inertia = self.mass * self.inertiaScale  # equals mass
        self.length = 2.5 #length
        self.axleWeightRatioFront = self.cgToRearAxle / self.length  # Percentage of vehicle weight on front
        self.axleWeightRatioRear = self.cgToFrontAxle / self.length  # Percentage of vehicle weight on rear

    def set_goal(self, x, y):
        self.goal_x = x
        self.goal_y = y

    def auto_steer(self):
        if self.goal_x is None or self.goal_y is None:
            return

        gx = self.goal_x
        gy = self.goal_y

        desired_heading = math.atan2(gy - self.cy, gx - self.cx)
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

        print("E{:.0f} = D{:.0f} - A{:.0f}".format(math.degrees(error), math.degrees(desired_heading), math.degrees(current_heading)))
        k_p = 4  # Proportional gain constant.
        if error < 0:
            self.right = k_p * normalise(math.fabs(error), 0, 2*math.pi)
            self.left = 0.0
        else:
            self.right = 0.0
            self.left = k_p * normalise(math.fabs(error), 0, 2*math.pi)



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

    def calculate_forces(self):
        # dt and fps calculation
        timestamp = time.time()
        dt = timestamp - self.last_update
        if dt == 0.0:
            return
        fps = 1.0 / dt
        self.last_update = timestamp

        # Calculate steering input autonomously.
        self.auto_steer()

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
        axleWeightFront = self.mass * (
                    self.axleWeightRatioFront * self.gravity - self.weightTransfer * self.lax * self.cgHeight / self.length)

        axleWeightRear = self.mass * (
                    self.axleWeightRatioRear * self.gravity + self.weightTransfer * self.lax * self.cgHeight / self.length)

        # Resulting velocity of the wheels as result of the yaw rate of the car body.
        # v = yawrate * r where r is distance from axle to CG and yawRate (angular velocity) in rad/s.
        yawSpeedFront = self.cgToFrontAxle * self.yaw_rate
        yawSpeedRear = -self.cgToRearAxle * self.yaw_rate

        # Calculate slip angles for front and rear wheels (a.k.a. alpha)
        slipAngleFront = math.atan2(self.lvy + yawSpeedFront, math.fabs(self.lvx)) - math.copysign(1,
                                                                                                   self.lvx) * self.steering_angle
        slipAngleRear = math.atan2(self.lvy + yawSpeedRear, math.fabs(self.lvx))

        tireGripFront = self.tireGrip
        tireGripRear = self.tireGrip # * (1.0 * (1.0 - self.lockGrip))  # reduce rear grip when ebrake is on

        frictionForceFront_cy = bound(-self.cornerStiffnessFront * slipAngleFront, -tireGripFront,
                                      tireGripFront) * axleWeightFront
        frictionForceRear_cy = bound(-self.cornerStiffnessRear * slipAngleRear, -tireGripRear,
                                     tireGripRear) * axleWeightRear

        #  Get amount of brake/throttle from our inputs
        brake = min(self.brake * self.brakeForce * self.eBrakeForce, self.brakeForce)
        throttle = self.throttle * self.engineForce

        #  Resulting force in local car coordinates.
        #  This is implemented as a RWD car only.
        tractionForce_cx = throttle - brake * math.copysign(1, self.lvx)
        tractionForce_cy = 0

        dragForce_cx = -self.rollResist * self.lvx - self.airResist * self.lvx * math.fabs(self.lvx)
        dragForce_cy = -self.rollResist * self.lvy - self.airResist * self.lvy * math.fabs(self.lvy)

        # total force in car coordinates
        totalForce_cx = dragForce_cx + tractionForce_cx
        totalForce_cy = dragForce_cy + tractionForce_cy + math.cos(
            self.steering_angle) * frictionForceFront_cy + frictionForceRear_cy

        # acceleration along car axes
        self.lax = totalForce_cx / self.mass  # forward/reverse accel
        self.lay = totalForce_cy / self.mass  # sideways accel

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
        angularTorque = (frictionForceFront_cy + tractionForce_cy) * self.cgToFrontAxle - frictionForceRear_cy * self.cgToRearAxle

        #  Sim gets unstable at very slow speeds, so just stop the boat
        if math.fabs(self.abs_velocity) < 0.5 and throttle == 0:
            self.vx = self.vy = self.abs_velocity = 0
            angularTorque = self.yaw_rate = 0

        angularAccel = angularTorque / self.inertia
        self.yaw_rate += angularAccel * dt
        self.heading += self.yaw_rate * dt
        # self.heading %= 2*math.pi

        #  finally we can update position
        self.cx += self.vx * dt
        self.cy += self.vy * dt

    def relative_speed(self):
        return bound(self.abs_velocity / self.max_speed, 0.0, 1.0)
