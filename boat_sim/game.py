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

SCREEN_WIDTH = 1900
SCREEN_HEIGHT = 900
SCREEN_TITLE = "Boat Sim"


class BoatSprite(arcade.Sprite):
    """ Player class """
    SPRITE_LENGTHS = {"small": 105, "medium": 179, "large": 368}
    IMAGES =  {"small" : "images/ship_small_b_body.png",
               "medium": "images/ship_medium_body_b2.png",
               "large" : "images/ship_large_body.png"}
    RIPPLES = {"small" : "images/water_ripple_small_000.png",
               "medium": "images/water_ripple_medium_000.png",
               "large" : "images/water_ripple_big_000.png"}
    OFFSET = 15

    def __init__(self, scale, center_x, center_y, sim, boat_type="medium"):
        """ Create vehicle model and setup sprites """

        # Call the parent init
        super().__init__(self.IMAGES[boat_type], scale)

        self.sim = sim

        self.length = self.SPRITE_LENGTHS[boat_type]
        self.vehicle_model = self.sim.add_boat(self.sim, center_x, center_y, boat_type=boat_type)

        self.center_x = center_x
        self.center_y = center_y

        # Adding sprite for ripple effects.
        self.ripple_sprite = arcade.Sprite(
            filename=self.RIPPLES[boat_type].format(boat_type, random.randint(0, 0),
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
        super().__init__(width, height, title, resizable=True)

        # Set the working directory (where we expect to find files) to the same
        # directory this .py file is in. You can leave this out of your own
        # code, but it is needed to easily run the examples using "python -m"
        # as mentioned at the top of this program.
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        # Simulator common to all agents
        self.sim = Sim()

        self.all_sprite_list = arcade.SpriteList()

        self.boat_sprites = []

        # Set the background color
        arcade.set_background_color(arcade.color.BLACK)

        # Config
        self.draw_potential_field = False
        self.potential_field_resolution = 100
        self.draw_goals = True
        self.draw_avoidance_boundaries = False
        self.draw_desired_heading = True
        self.debug = True

        # Human control
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        self.background_textures = []

        self.timestamp = time.time()
        self.frame_counter = 0

    def load_background_textures(self):
        background_path = "images/background_frames2/"
        frames = 30
        for i in range(1, frames):
            if i % 100 == 0:
                print("{}%".format(100*i/frames))
            texture = arcade.load_texture(background_path+"scene{:05d}.png".format(i))
            self.background_textures.append(texture)

    def setup_borders(self, num_boats):
        """
        Boats will have one of 4 different colours, associated to each edge of the screen.
        The colour represents the boat's destination.
        1: blue -> left
        2: red -> top
        3: green -> bottom
        4: yellow -> right
        :param num_boats: Number of boats to be generated.
        :return:
        """
        border_thickness = int(SCREEN_WIDTH / 10)
        min_distance_between_goals = 50
        min_distance_between_starting_positions = 25
        goals = []
        starting_positions = []
        colour = 0
        side = 0
        angle = 0

        def too_close(position, container, threshold):
            for p in container:
                if math.dist(position, p) < threshold:
                    return True
            return False

        for i in range(num_boats):
            colour = random.randint(1, 4)
            side = colour
            # Get a starting side different from that colour.
            while side == colour:
                side = random.randint(1, 4)
            while True:
                if colour == 1: # Blue (left)
                    goal_x = random.randint(0, border_thickness)
                    goal_y = random.randint(0, SCREEN_HEIGHT)
                elif colour == 2: # Red (top)
                    goal_x = random.randint(0, SCREEN_WIDTH)
                    goal_y = random.randint(SCREEN_HEIGHT - border_thickness, SCREEN_HEIGHT)
                elif colour == 3: # Green (bottom)
                    goal_x = random.randint(0, SCREEN_WIDTH)
                    goal_y = random.randint(0, border_thickness)
                else: # Yellow (right)
                    goal_x = random.randint(SCREEN_WIDTH - border_thickness, SCREEN_WIDTH)
                    goal_y = random.randint(0, SCREEN_HEIGHT)
                # Ensure minimum distance from other goals.
                if not too_close((goal_x, goal_y), goals, min_distance_between_goals):
                    break
            
            while True:
                if side == 1:  # Blue (left)
                    start_x = random.randint(0, border_thickness)
                    start_y = random.randint(0, SCREEN_HEIGHT)
                    angle = math.pi
                elif side == 2:  # Red (top)
                    start_x = random.randint(0, SCREEN_WIDTH)
                    start_y = random.randint(SCREEN_HEIGHT - border_thickness, SCREEN_HEIGHT)
                    angle = math.pi/2
                elif side == 3:  # Green (bottom)
                    start_x = random.randint(0, SCREEN_WIDTH)
                    start_y = random.randint(0, border_thickness)
                    angle = -math.pi/2
                else:  # Yellow (right)
                    start_x = random.randint(SCREEN_WIDTH - border_thickness, SCREEN_WIDTH)
                    start_y = random.randint(0, SCREEN_HEIGHT)
                    angle = 0
                # Ensure minimum distance from other starts.
                if not too_close((start_x, start_y), starting_positions, min_distance_between_starting_positions):
                    break

            # Choose a boat size given the probability distribution below.
            size_probabilities = {"small": 0.6,
                                  "medium": 0.35,
                                  "large": 0.05}
            size = random.choices(list(size_probabilities.keys()), list(size_probabilities.values()), k=1)[0]
            boat_sprite = BoatSprite(SPRITE_SCALING, start_x, start_y, self.sim, boat_type=size)
            boat_sprite.vehicle_model.set_goal(goal_x, goal_y)
            boat_sprite.vehicle_model.heading = angle
            goals.append((goal_x, goal_y))
            starting_positions.append((start_x, start_y))
            boat_sprite.vehicle_model.goal_colour = colour
            self.boat_sprites.append(boat_sprite)
            self.all_sprite_list.extend([boat_sprite, boat_sprite.ripple()])

    def setup_random(self, num_boats):
        for i in range(num_boats):
            cx = random.randint(0, SCREEN_WIDTH)
            cy = random.randint(0, SCREEN_HEIGHT)
            boat_sprite = BoatSprite(SPRITE_SCALING, cx, cy, self.sim)
            goal_x = random.randint(0, SCREEN_WIDTH)
            goal_y = random.randint(0, SCREEN_HEIGHT)
            boat_sprite.vehicle_model.set_goal(goal_x, goal_y)
            self.boat_sprites.append(boat_sprite)
            self.all_sprite_list.extend([boat_sprite, boat_sprite.ripple()])

    def setup_manual3(self):
        # Set up boat A
        center_x = 300
        center_y = 300
        boat_sprite_a = BoatSprite(SPRITE_SCALING, center_x, center_y, self.sim, boat_type="large")
        goal_x = 400
        goal_y = 300
        boat_sprite_a.vehicle_model.set_goal(goal_x, goal_y)
        boat_sprite_a.vehicle_model.heading = math.pi/2

        self.boat_sprites = []
        self.boat_sprites.extend([boat_sprite_a])

        self.all_sprite_list.extend([boat_sprite_a, boat_sprite_a.ripple()])

    def setup_manual(self):
        # Set up boat A
        center_x = 300
        center_y = 300
        boat_sprite_a = BoatSprite(SPRITE_SCALING, center_x, center_y, self.sim, boat_type="medium")
        goal_x = random.randint(500, SCREEN_WIDTH)
        goal_y = random.randint(600, SCREEN_HEIGHT)
        boat_sprite_a.vehicle_model.set_goal(goal_x, goal_y)

        # Set up boat B
        center_x = 750
        center_y = 750
        boat_sprite_b = BoatSprite(SPRITE_SCALING, center_x, center_y, self.sim, boat_type="medium")
        goal_x = random.randint(0, 400)
        goal_y = random.randint(0, 400)
        boat_sprite_b.vehicle_model.set_goal(goal_x, goal_y)
        boat_sprite_b.vehicle_model.heading = -3*math.pi/4

        # Set up boat C
        center_x = 800
        center_y = 500
        boat_sprite_c = BoatSprite(SPRITE_SCALING, center_x, center_y, self.sim, boat_type="medium")
        goal_x = random.randint(000, 100)
        goal_y = random.randint(400, 600)
        boat_sprite_c.vehicle_model.set_goal(goal_x, goal_y)
        boat_sprite_c.vehicle_model.heading = math.pi / 2

        self.boat_sprites = []
        self.boat_sprites.extend([boat_sprite_a, boat_sprite_b, boat_sprite_c])

        self.all_sprite_list.extend([boat_sprite_a, boat_sprite_b, boat_sprite_c,
                                     boat_sprite_a.ripple(), boat_sprite_b.ripple(), boat_sprite_c.ripple()])

    def setup_manual2(self):
        # Set up boat A
        center_x = 300
        center_y = 300
        boat_sprite_a = BoatSprite(SPRITE_SCALING, center_x, center_y, self.sim)
        goal_x = random.randint(730, 770)
        goal_y = random.randint(730, 770)
        boat_sprite_a.vehicle_model.set_goal(goal_x, goal_y)
        boat_sprite_a.vehicle_model.heading = -math.pi / 2

        # Set up boat B
        center_x = 750
        center_y = 750
        boat_sprite_b = BoatSprite(SPRITE_SCALING, center_x, center_y, self.sim)
        goal_x = random.randint(280, 320)
        goal_y = random.randint(280, 320)
        boat_sprite_b.vehicle_model.set_goal(goal_x, goal_y)
        boat_sprite_b.vehicle_model.heading = -math.pi / 2

        self.boat_sprites = []
        self.boat_sprites.extend([boat_sprite_a, boat_sprite_b])

        self.all_sprite_list.extend([boat_sprite_a, boat_sprite_b, boat_sprite_a.ripple(), boat_sprite_b.ripple()])

    def on_draw(self):
        """
        Render the screen.
        """

        timestamp = time.time()
        # fps = 1.0 / (timestamp - self.timestamp)
        self.timestamp = timestamp
        # print("FPS: ", fps)
        self.frame_counter += 1
        slow_factor = 3
        frame = self.frame_counter % (slow_factor * len(self.background_textures))
        self.frame_counter = frame
        frame = int(frame/slow_factor)

        # This command has to happen before we start drawing
        arcade.start_render()

        # Draw the background texture
        # arcade.draw_lrwh_rectangle_textured(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background)
        arcade.draw_lrwh_rectangle_textured(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background_textures[frame])

        # Draw all the sprites.
        self.all_sprite_list.draw()
        i = 1

        def draw_arrow(x1, y1, angle, length, colour, thickness = 1.0):
            x2 = x1 + length * math.cos(angle)
            y2 = y1 + length * math.sin(angle)
            arcade.draw_line(x1, y1, x2, y2, colour, thickness)

            # Draw arrowheads.
            head_size = 5
            dx = x1 - x2
            dy = y1 - y2
            norm = math.sqrt(dx * dx + dy * dy)
            udx = dx / norm  # Normalised x.
            udy = dy / norm
            angle = math.pi / 6
            ax = udx * math.cos(angle) - udy * math.sin(angle)
            ay = udx * math.sin(angle) + udy * math.cos(angle)
            bx = udx * math.cos(angle) + udy * math.sin(angle)
            by = -udx * math.sin(angle) + udy * math.cos(angle)
            arcade.draw_line(x2, y2, x2 + head_size * ax, y2 + head_size * ay, colour, thickness)
            arcade.draw_line(x2, y2, x2 + head_size * bx, y2 + head_size * by, colour, thickness)

        # Draw goals and indices.
        if self.draw_goals:
            for boat in self.boat_sprites:
                colour_id = boat.vehicle_model.goal_colour
                if colour_id == 1:
                    colour = arcade.color.BLUE
                elif colour_id == 2:
                    colour = arcade.color.RED
                elif colour_id == 3:
                    colour = arcade.color.GREEN
                elif colour_id == 4:
                    colour = arcade.color.YELLOW
                else:
                    colour = arcade.color.BLACK

                if boat.vehicle_model.at_destination:
                    colour = arcade.color.GRAY
                boat_x, boat_y = boat.vehicle_model.position
                goal_x, goal_y = boat.vehicle_model.goal
                arcade.draw_circle_filled(goal_x, goal_y, 10, colour)
                text_colour = arcade.color.WHITE if colour_id < 2 else arcade.color.BLACK
                arcade.draw_text(str(i), goal_x, goal_y, text_colour, 15)
                arcade.draw_text(str(i), boat_x, boat_y, colour, 15)
                i += 1

        # Draw potential field.
        if self.draw_potential_field:
            resolution = self.potential_field_resolution
            for x1 in range(0, SCREEN_WIDTH, resolution):
                for y1 in range(0, SCREEN_HEIGHT, resolution):
                    v = self.sim.get_velocity((x1, y1), 0)
                    thickness = 1.0
                    length = 20
                    angle = math.atan2(v[1], v[0])
                    x2 = x1 + (v[0] * length)
                    y2 = y1 + (v[1] * length)
                    draw_arrow(x1, y1, angle, length, arcade.color.BLACK, thickness)

        if self.draw_avoidance_boundaries:
            for boat in self.boat_sprites:
                if boat.vehicle_model.at_destination:
                    continue
                cx, cy = boat.vehicle_model.position
                min_distance = self.sim.avoidance_min_distance
                max_distance = self.sim.avoidance_max_distance
                arcade.draw_circle_outline(cx, cy, min_distance, arcade.color.WHITE, 1)
                arc_angle = math.degrees(boat.vehicle_model.heading) + 90
                arcade.draw_arc_outline(cx, cy, 2*max_distance, 2*max_distance, arcade.color.WHITE, 0, 180, 1.5, arc_angle, 30)

        if self.debug:
            for boat in self.boat_sprites:
                if boat.vehicle_model.at_destination:
                    continue
                cx, cy = boat.vehicle_model.position
                throttle = boat.vehicle_model.throttle
                brake = boat.vehicle_model.brake
                speed = boat.vehicle_model.abs_velocity
                rel_hdg = boat.vehicle_model.DEBUG_relative_heading
                dist = boat.vehicle_model.distance_to_goal
                l = boat.vehicle_model.left
                r = boat.vehicle_model.right
                debug = "{}\nTHR:{:.2f}\nBRK:{:.2f}\nSPD:{:.2f}\nDIST:{}\nL:{:.2f}|R:{:.2f}".format(boat.vehicle_model.DEBUG_message,
                                                                                 throttle, brake, speed, int(dist), l, r)
                arcade.draw_text(debug, cx, cy + 40, arcade.color.RED, 15)

        if self.draw_desired_heading:
            for boat in self.boat_sprites:
                if boat.vehicle_model.at_destination:
                    continue
                cx, cy = boat.vehicle_model.position
                desired_hdg = boat.vehicle_model.DEBUG_desired_heading
                length = 40
                draw_arrow(cx, cy, desired_hdg, length, arcade.color.RED, thickness=2.0)

    def on_update(self, delta_time):
        """ Movement and game logic """

        # Call update on all sprites (The sprites don't do much in this
        # example though.)

        boat_sprite = self.all_sprite_list[0]

        boat_sprite.vehicle_model.reset_inputs()

        if self.up_pressed and not self.down_pressed:
            boat_sprite.vehicle_model.throttle = 1.0
        elif self.down_pressed and not self.up_pressed:
            boat_sprite.vehicle_model.brake = 1.0
        if self.left_pressed and not self.right_pressed:
            boat_sprite.vehicle_model.left = 1.0
        elif self.right_pressed and not self.left_pressed:
            boat_sprite.vehicle_model.right = 1.0

        self.all_sprite_list.update()

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

    def setup(self):
        """ Set up the game and initialize the variables. """

        # Sprite lists
        # self.background = arcade.load_texture("images/water_background.png")
        # self.background = arcade.load_texture("images/animated.gif")
        self.load_background_textures()
        self.setup_borders(30)
        # self.setup_manual()

def main():
    """ Main method """
    window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
