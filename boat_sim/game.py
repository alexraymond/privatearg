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

from vehicle import VehicleModel

SPRITE_SCALING = 0.5

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 1024
SCREEN_TITLE = "Boat Sim"

MOVEMENT_SPEED = 5
ANGLE_SPEED = 5


class BoatSprite(arcade.Sprite):
    """ Player class """
    BOAT_SIZE = "medium"

    def __init__(self, image, scale, center_x, center_y):
        """ Set up the player """
        self.vehicle_model = VehicleModel(center_x, center_y)

        # Adding sprite for ripple effects.
        self.ripple_sprite = arcade.Sprite(
            filename="images/water_ripple_{}_00{}.png".format(self.BOAT_SIZE, random.randint(0, 5),
                                                              center_x=center_x,
                                                              center_y=center_y, hit_box_algorithm="None"))
        self.ripple_sprite.scale = SPRITE_SCALING

        # Call the parent init
        super().__init__(image, scale)

        # Create a variable to hold our speed. 'angle' is created by the parent
        self.speed = 0

    def update_ripple_sprite(self, angle, center_x, center_y):
        self.ripple_sprite.angle = angle
        self.ripple_sprite.center_x = center_x
        self.ripple_sprite.center_y = center_y
        self.ripple_sprite.alpha = math.fabs(self.vehicle_model.relative_speed() * 255)

        self.ripple_sprite.update()

    def update(self):
        # Update vehicle physics
        self.vehicle_model.update_pos()

        # Rotate the ship
        self.angle = self.vehicle_model.heading

        # Use math to find our change based on our speed and angle
        self.center_x = self.vehicle_model.center_x
        self.center_y = self.vehicle_model.center_y

        self.update_ripple_sprite(self.angle, self.center_x, self.center_y)


class MyGame(arcade.Window):
    """
    Main application class.
    """

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

        # Variables that will hold sprite lists
        self.boat_sprite_list = None

        # Set up the player info
        self.boat_sprite = None

        # Set the background color
        arcade.set_background_color(arcade.color.BLACK)

    def setup(self):
        """ Set up the game and initialize the variables. """

        # Sprite lists
        self.boat_sprite_list = arcade.SpriteList()
        self.background = arcade.load_texture("images/water_background.png")

        # Set up the player
        center_x = SCREEN_WIDTH / 2
        center_y = SCREEN_HEIGHT / 2
        self.boat_sprite = BoatSprite("images/ship_medium_body.png", SPRITE_SCALING, center_x, center_y)
        self.boat_sprite.center_x = center_x
        self.boat_sprite.center_y = center_y
        self.boat_sprite_list.append(self.boat_sprite)

    def on_draw(self):
        """
        Render the screen.
        """

        # This command has to happen before we start drawing
        arcade.start_render()

        # Draw the background texture
        arcade.draw_lrwh_rectangle_textured(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background)

        # Draw all the sprites.
        self.boat_sprite_list.draw()
        self.boat_sprite.ripple_sprite.draw()

    def on_update(self, delta_time):
        """ Movement and game logic """

        # Call update on all sprites (The sprites don't do much in this
        # example though.)
        self.boat_sprite_list.update()

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        # Forward/back
        if key == arcade.key.UP:
            self.boat_sprite.vehicle_model.manual_input(acceleration=0.1, steering=0.0)
        elif key == arcade.key.DOWN:
            self.boat_sprite.vehicle_model.manual_input(acceleration=-0.1, steering=0.0)

        # Rotate left/right
        elif key == arcade.key.LEFT:
            self.boat_sprite.vehicle_model.manual_input(acceleration=0.0, steering=15.0)
        elif key == arcade.key.RIGHT:
            self.boat_sprite.vehicle_model.manual_input(acceleration=0.0, steering=-15.0)

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """
        pass

        # if key == arcade.key.UP or key == arcade.key.DOWN:
        #     self.player_sprite.speed = 0
        # elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
        #     self.player_sprite.change_angle = 0


def main():
    """ Main method """
    window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
