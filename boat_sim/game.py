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
import datetime
import sys
import json
import numpy as np

from vehicle_model import BoatModel
from sim import Sim
from utils import *

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

    def __init__(self, game, center_x, center_y, sim, boat_type="medium"):
        """ Create vehicle model and setup sprites """

        self.base_sim = sim
        self.game_handle = game

        # Call the parent init
        super().__init__(self.IMAGES[boat_type], self.game_handle.sprite_scaling)

        self.length = self.SPRITE_LENGTHS[boat_type]
        self.vehicle_model = self.base_sim.add_boat(self.base_sim, center_x, center_y, boat_type=boat_type)

        self.center_x = center_x
        self.center_y = center_y

        # Adding sprite for ripple effects.
        self.ripple_sprite = arcade.Sprite(
            filename=self.RIPPLES[boat_type].format(boat_type, random.randint(0, 0),
                                              center_x=center_x,
                                              center_y=center_y, hit_box_algorithm="None"))
        self.ripple_sprite.scale = self.game_handle.sprite_scaling + 0.1  # FIXME: Workaround to avoid overlap


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
        self.center_x, self.center_y = self.vehicle_model.get_position(self.game_handle.zoom_factor)

        self.update_ripple_sprite(self.radians, self.center_x, self.center_y)


class MyGame(arcade.Window):
    """
    Main application class.
    """
    SIZES = {"small": 105, "medium": 179, "large": 368}

    def __init__(self, config_file_path):
        """
        Initializer
        """

        self.all_configs = None

        with open(config_file_path) as file:
            self.all_configs = json.load(file)

        graphics_config = self.all_configs["sim"]["graphics"]

        width = graphics_config["width"]
        height = graphics_config["height"]
        title = graphics_config["window_title"]
        self.sprite_scaling = graphics_config["sprite_scaling"]
        self.zoom_factor = graphics_config["zoom_factor"]
        self.viewport_left = 0
        self.viewport_right = width
        self.viewport_bottom = 0
        self.viewport_top = height
        self.viewport_zoom = 1

        # Call the parent class initializer
        super().__init__(width, height, title, resizable=True)

        # Set the working directory (where we expect to find files) to the same
        # directory this .py file is in. You can leave this out of your own
        # code, but it is needed to easily run the examples using "python -m"
        # as mentioned at the top of this program.
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        # Base simulator common to all agents
        self.base_sim = Sim(sim_config=self.all_configs["sim"])

        self.all_sprite_list = arcade.SpriteList()

        self.boat_sprites = []

        # Set the background color
        arcade.set_background_color(arcade.color.BLACK)

        # Config
        self.draw_potential_field = graphics_config["potential_field"]["render"]
        self.potential_field_resolution = graphics_config["potential_field"]["resolution"]
        self.draw_goals = graphics_config["goals"]
        self.draw_avoidance_boundaries = graphics_config["avoidance_boundaries"]
        self.draw_desired_heading = graphics_config["desired_heading"]
        self.draw_names = graphics_config["names"]
        self.draw_trajectories = graphics_config["trajectories"]
        self.debug = graphics_config["debug_info"]

        self.background_textures = []

        self.timestamp = time.time()
        self.frame_counter = 0

    def load_background_textures(self):
        background_config = self.all_configs["sim"]["graphics"]["background"]
        background_path = background_config["path"]
        frames = background_config["frames"]
        for i in range(1, frames):
            if i % 100 == 0:
                print("{}%".format(100*i/frames))
            texture = arcade.load_texture(background_path+"scene{:05d}.png".format(i))
            self.background_textures.append(texture)

    def load_boats(self):
        boats = self.all_configs["sim"]["boats"]
        for boat in boats:
            boat_sprite = BoatSprite(self, boat["start_x"], boat["start_y"], self.base_sim, boat["size"])
            boat_sprite.vehicle_model.set_goal(boat["goal_x"], boat["goal_y"])
            boat_sprite.vehicle_model.name = boat["name"]
            boat_sprite.vehicle_model.heading = math.radians(boat["initial_heading"])
            boat_sprite.vehicle_model.goal_colour = boat["colour"]
            boat_sprite.vehicle_model.write_trajectories = self.all_configs["sim"]["write_trajectories"]
            self.boat_sprites.append(boat_sprite)
            self.all_sprite_list.extend([boat_sprite, boat_sprite.ripple()])

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
        width = self.all_configs["sim"]["graphics"]["width"]
        height = self.all_configs["sim"]["graphics"]["height"]
        arcade.draw_lrwh_rectangle_textured(0, 0, width, height, self.background_textures[frame])

        # Draw all the sprites.
        self.all_sprite_list.draw()

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
                if colour_id == "blue":
                    colour = arcade.color.LIGHT_BLUE
                elif colour_id == "red":
                    colour = arcade.color.RED
                elif colour_id == "green":
                    colour = arcade.color.GREEN
                elif colour_id == "yellow":
                    colour = arcade.color.YELLOW
                else:
                    colour = arcade.color.BLACK

                if boat.vehicle_model.at_destination:
                    colour = arcade.color.GRAY
                boat_x, boat_y = boat.vehicle_model.get_position(self.zoom_factor)
                goal_x, goal_y = boat.vehicle_model.get_goal(self.zoom_factor)
                arcade.draw_circle_filled(goal_x, goal_y, 10, colour)
                if self.draw_trajectories:
                    trajectory = boat.vehicle_model.trajectory
                    for i in range(0, len(trajectory), 30):
                        arcade.draw_point(trajectory[i][0] * self.zoom_factor, trajectory[i][1] * self.zoom_factor, colour, 3)
                if self.draw_names:
                    name = boat.vehicle_model.name
                    text_colour = arcade.color.WHITE if colour_id == "blue" or colour_id == "red" else arcade.color.BLACK
                    arcade.draw_text(name, goal_x, goal_y, text_colour, 15)
                    arcade.draw_text(name, boat_x, boat_y, colour, 15)


        # Draw potential field.
        if self.draw_potential_field:
            resolution = self.potential_field_resolution
            for x1 in range(0, SCREEN_WIDTH, resolution):
                for y1 in range(0, SCREEN_HEIGHT, resolution):
                    v = self.base_sim.get_velocity((x1, y1), 0)
                    thickness = 1.0
                    length = 20
                    angle = math.atan2(v[1], v[0])
                    x2 = x1 + (v[0] * length)
                    y2 = y1 + (v[1] * length)
                    draw_arrow(x1, y1, angle, length, arcade.color.BLACK, thickness)

        # Draw avoidance boundaries.
        if self.draw_avoidance_boundaries:
            for boat in self.boat_sprites:
                if boat.vehicle_model.at_destination:
                    continue
                cx, cy = boat.vehicle_model.get_position(self.zoom_factor)
                min_distance = self.base_sim.avoidance_min_distance
                max_distance = min_distance + (boat.vehicle_model.relative_speed() * self.base_sim.avoidance_max_distance)
                max_distance = bound(max_distance, min_distance, self.base_sim.avoidance_max_distance)
                # Adjust for zoom factor.
                min_distance *= self.zoom_factor
                max_distance *= self.zoom_factor
                arcade.draw_circle_outline(cx, cy, min_distance, arcade.color.WHITE, 1)
                arc_angle = math.degrees(boat.vehicle_model.heading) + 90
                arcade.draw_arc_outline(cx, cy, 2*max_distance, 2*max_distance, arcade.color.WHITE, 0, 180, 1.5, arc_angle, 30)

        if self.draw_desired_heading:
            for boat in self.boat_sprites:
                if boat.vehicle_model.at_destination:
                    continue
                cx, cy = boat.vehicle_model.get_position(self.zoom_factor)
                desired_hdg = boat.vehicle_model.DEBUG_desired_heading
                length = 40
                draw_arrow(cx, cy, desired_hdg, length, arcade.color.RED, thickness=2.0)

        if self.debug:
            for boat in self.boat_sprites:
                if boat.vehicle_model.at_destination:
                    continue
                cx, cy = boat.vehicle_model.get_position(self.zoom_factor)
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



    def on_update(self, delta_time):
        """ Movement and game logic """

        # Call update on all sprites (The sprites don't do much in this
        # example though.)

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
        self.load_boats()
        # self.setup_borders(10)
        # self.setup_manual3()

    def set_viewport(self, left: float, right: float, bottom: float, top: float):
        self.viewport_left, self.viewport_right, self.viewport_bottom, self.viewport_top = left, right, bottom, top
        arcade.set_viewport(left, right, bottom, top)


    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        self.viewport_zoom = bound(self.viewport_zoom + (scroll_y / 10.0), 1.0, 5.0)

        screen_width = self.all_configs["sim"]["graphics"]["width"]
        screen_height = self.all_configs["sim"]["graphics"]["height"]

        excess_left = bound(x - ((screen_width / self.viewport_zoom) / 2), -screen_width, 0)
        excess_right = bound(x + ((screen_width / self.viewport_zoom) / 2) - screen_width, 0, screen_width)
        excess_bottom = bound(y - ((screen_height / self.viewport_zoom) / 2), -screen_height, 0)
        excess_top = bound(y + ((screen_height / self.viewport_zoom) / 2) - screen_height, 0, screen_height)

        left = bound(x - ((screen_width / self.viewport_zoom) / 2) - excess_right, 0, screen_width)
        right = bound(x + ((screen_width / self.viewport_zoom) / 2) - excess_left, 0, screen_width)
        bottom = bound(y - ((screen_height / self.viewport_zoom) / 2) - excess_top, 0, screen_height)
        top = bound(y + ((screen_height / self.viewport_zoom) / 2) - excess_bottom, 0, screen_height)

        self.set_viewport(left, right, bottom, top)

    def on_mouse_drag(self, x: float, y: float, dx: float, dy: float, buttons: int, modifiers: int):
        screen_width = self.all_configs["sim"]["graphics"]["width"]
        screen_height = self.all_configs["sim"]["graphics"]["height"]
        left, right, bottom, top = self.viewport_left, self.viewport_right, self.viewport_bottom, self.viewport_top

        excess_left = bound(left + dx, -screen_width, 0)
        excess_right = bound(right + dx - screen_width, 0, screen_width)
        excess_bottom = bound(bottom + dy, -screen_height, 0)
        excess_top = bound(top + dy - screen_height, 0, screen_height)

        left = bound(left + dx - excess_right, 0, screen_width)
        right = bound(right + dx - excess_left, 0, screen_width)
        bottom = bound(bottom + dy - excess_top, 0, screen_height)
        top = bound(top + dy - excess_bottom, 0, screen_height)

        self.set_viewport(left, right, bottom, top)


def run(config_file):
    """ Main method """
    with open(config_file) as file:
        data = json.load(file)
    headless = data["sim"]["graphics"]["headless"]
    num_strategies = len(data["sim"]["dialogue_results"])
    num_budgets = len(data["sim"]["dialogue_results"]["ArgStrategy.RANDOM_CHOICE_PRIVATE"])
    start = time.time()
    results_path = "results/"
    if headless:
        boats_dict = data["sim"]["boats"]
        for strategy in data["sim"]["dialogue_results"].keys():
            path = results_path+strategy
            os.makedirs(path)
            for budget in data["sim"]["dialogue_results"][strategy]:
                sim = Sim(data["sim"], budget=int(budget), strategy=strategy)
                sim.load_boats(boats_dict)
                frame_counter = 0
                while sim.is_running:
                    frame_counter += 1
                    if frame_counter % 1000 == 0:
                        print("Simulated {} frames.".format(frame_counter))
                    for boat in sim.boats:
                        boat.simulate_kinematics()
                end = time.time()
                print("Time elapsed: {:.2f} seconds".format(end - start))
                return sim.results_filename

    else:
        window = MyGame(config_file)
        window.setup()
        arcade.run()


# def run(config_file):
#     """ Main method """
#     with open(config_file) as file:
#         data = json.load(file)
#     headless = data["sim"]["graphics"]["headless"]
#     start = time.time()
#     if headless:
#         boats_dict = data["sim"]["boats"]
#         sim = Sim(data["sim"])
#         sim.load_boats(boats_dict)
#         frame_counter = 0
#         while sim.is_running:
#             frame_counter += 1
#             if frame_counter % 1000 == 0:
#                 print("Simulated {} frames.".format(frame_counter))
#             for boat in sim.boats:
#                 boat.simulate_kinematics()
#         end = time.time()
#         print("Time elapsed: {:.2f} seconds".format(end - start))
#         return sim.results_filename
#
#     else:
#         window = MyGame(config_file)
#         window.setup()
#         arcade.run()


