"""
Move Sprite by Angle

Simple program to show basic sprite usage.

Artwork from https://opengameart.org/content/ships-with-ripple-effect

If Python and Arcade are installed, this example can be run from the command line with:
python -m arcade.examples.sprite_move_angle
"""
import arcade
import os
import math
import random
import time
import numpy as np

from vehicle_model import BoatModel
from sim import Sim

SPRITE_SCALING = 0.25

SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 1080
SCREEN_TITLE = "Boat Sim"

MOVEMENT_SPEED = 5
ANGLE_SPEED = 5


class BoatSprite(arcade.Sprite):
    """ Player class """
    SIZES = {"small": 105, "medium": 179, "large": 368}
    OFFSET = 15

    def __init__(self, image, scale, center_x, center_y, sim, size_label="medium"):
        """ Create vehicle model and setup sprites """

        # Call the parent init
        super().__init__(image, scale)

        self.sim = sim

        self.length = self.SIZES[size_label]
        self.vehicle_model = self.sim.add_boat(self.sim, center_x, center_y, length=self.length)

        self.center_x = center_x
        self.center_y = center_y

        # Adding sprite for ripple effects.
        self.ripple_sprite = arcade.Sprite(
            filename="images/water_ripple_{}_00{}.png".format(size_label, random.randint(0, 0),
                                                              center_x=center_x,
                                                              center_y=center_y, hit_box_algorithm="None"))
        self.ripple_sprite.scale = SPRITE_SCALING + 0.1  # FIXME: Workaround to avoid overlap


        # Create a variable to hold our speed. 'angle' is created by the parent
        self.speed = 0

    def ripple(self):
        return self.ripple_sprite

    def update_ripple_sprite(self, radians, center_x, center_y):
        self.ripple_sprite.radians = radians
        self.ripple_sprite.center_x = center_x + self.OFFSET * math.cos(radians)
        self.ripple_sprite.center_y = center_y + self.OFFSET * math.sin(radians)
        self.ripple_sprite.alpha = math.fabs(self.vehicle_model.relative_speed() * 255)

        self.ripple_sprite.update()

    def update(self):
        # Update vehicle physics
        self.vehicle_model.simulate_kinematics()

        # Rotate the ship
        self.radians = self.vehicle_model.heading
        # print("angle: {}".format(self.angle))

        # Use math to find our change based on our speed and angle
        self.center_x, self.center_y = self.vehicle_model.position

        self.update_ripple_sprite(self.radians, self.center_x, self.center_y)


class MyGame(arcade.Window):
    """
    Main application class.
    """
    SIZES = {"small": 105, "medium": 179, "large": 368}

    def __init__(self, width, height, title):
        """
        Initializer
        """

        # Call the parent class initializer
        super().__init__(width, height, title)

        # Set the working directory (where we expect to find files) to the same
        # directory this .py file is in. You can leave this out of your own
        # code, but it is needed to easily run the examples using "python -m"
        # as mentioned at the top of this program.
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        # Simulator common to all agents
        self.sim = Sim()

        self.boat_sprite_list = None

        self.visual_elements_sprite_list = None

        # Set the background color
        arcade.set_background_color(arcade.color.BLACK)

        # Config
        self.draw_potential_field = True

        # Human control
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        self.timestamp = time.time()



    def setup(self):
        """ Set up the game and initialize the variables. """

        # Sprite lists
        self.boat_sprite_list = arcade.SpriteList()
        self.background = arcade.load_texture("images/water_background.png")

        # Set up the player
        center_x = SCREEN_WIDTH / 2
        center_y = SCREEN_HEIGHT / 2
        boat_sprite = BoatSprite("images/ship_medium_body_b2.png", SPRITE_SCALING, center_x, center_y, self.sim)
        self.boat_sprite_list.extend([boat_sprite, boat_sprite.ripple()])

        self.test_goal_x = random.randint(0, SCREEN_WIDTH)
        self.test_goal_y = random.randint(0, SCREEN_HEIGHT)
        boat_sprite.vehicle_model.set_goal(self.test_goal_x, self.test_goal_y)

    def on_draw(self):
        """
        Render the screen.
        """

        timestamp = time.time()
        fps = 1.0 / (timestamp - self.timestamp)
        self.timestamp = timestamp
        print("FPS: ", fps)

        # This command has to happen before we start drawing
        arcade.start_render()

        # Draw the background texture
        arcade.draw_lrwh_rectangle_textured(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background)

        # Draw all the sprites.
        self.boat_sprite_list.draw()
        arcade.draw_circle_filled(self.test_goal_x, self.test_goal_y, 10, arcade.color.RED)

        # Draw potential field.
        if self.draw_potential_field:
            resolution = 30
            for i in range(0, SCREEN_WIDTH, resolution):
                for j in range(0, SCREEN_HEIGHT, resolution):
                    v = self.sim.get_velocity((i, j), 0)
                    #x1y1, x2y2
                    size = 20
                    x2 = i + (v[0] * size)
                    y2 = j + (v[1] * size)
                    arcade.draw_line(i, j, x2, y2, arcade.color.BLACK, 2)

    def on_update(self, delta_time):
        """ Movement and game logic """

        # Call update on all sprites (The sprites don't do much in this
        # example though.)

        boat_sprite = self.boat_sprite_list[0]

        boat_sprite.vehicle_model.reset_inputs()

        if self.up_pressed and not self.down_pressed:
            boat_sprite.vehicle_model.throttle = 1.0
        elif self.down_pressed and not self.up_pressed:
            boat_sprite.vehicle_model.brake = 1.0
        if self.left_pressed and not self.right_pressed:
            boat_sprite.vehicle_model.left = 1.0
        elif self.right_pressed and not self.left_pressed:
            boat_sprite.vehicle_model.right = 1.0

        self.boat_sprite_list.update()

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        if key == arcade.key.UP:
            self.up_pressed = True
        elif key == arcade.key.DOWN:
            self.down_pressed = True
        # elif key == arcade.key.LEFT:
        #     self.left_pressed = True
        # elif key == arcade.key.RIGHT:
        #     self.right_pressed = True

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.UP:
            self.up_pressed = False
        elif key == arcade.key.DOWN:
            self.down_pressed = False
        elif key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False

def main():
    """ Main method """
    window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
