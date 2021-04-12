import math

class VehicleModel:
    def __init__(self, center_x=0, center_y=0):
        self.MAX_SPEED = 1.0
        self.heading = 0
        self.center_x = center_x
        self.center_y = center_y
        self.speed = 0

    def manual_input(self, acceleration, steering):
        self.speed += acceleration
        if self.speed > self.MAX_SPEED:
            self.speed = self.MAX_SPEED
        self.heading += steering
        print("Speed: {} | Heading: {}".format(self.speed, self.heading))

    def update_pos(self):
        self.center_x += -self.speed * math.sin(math.radians(self.heading))
        self.center_y += self.speed * math.cos(math.radians(self.heading))

    def relative_speed(self):
        return self.speed / self.MAX_SPEED

