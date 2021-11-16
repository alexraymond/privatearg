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

"""
Rendering constants.gg
"""
SPRITE_SCALING = 0.25
SCREEN_WIDTH = 1900
SCREEN_HEIGHT = 900
SCREEN_TITLE = "Boat Sim"


class BoatSprite(arcade.Sprite):
    """
    This class contains the graphical representation of the boat on the screen.
    BoatSprites are loaded by BoatSim.
    """
    SPRITE_LENGTHS = {"small": 105, "medium": 179, "large": 368}
    IMAGES =  {"small" : "images/ship_small_b_body.png",
               "medium": "images/ship_medium_body_b2.png",
               "large" : "images/ship_large_body.png"}
    RIPPLES = {"small" : "images/water_ripple_small_000.png",
               "medium": "images/water_ripple_medium_000.png",
               "large" : "images/water_ripple_big_000.png"}
    RIPPLE_OFFSET = 15

    def __init__(self, game, boat_id, center_x, center_y, sim, boat_type="medium"):
        """ Create vehicle model and setup sprites
        :param game: Instance of the BoatGUI class representing the game.
        :param boat_id: Boat ID associated with the sprite.
        :param center_x: Center X position of the boat.
        :param center_y: Center Y position of the boat.
        :param sim: Instance of the Sim class representing the detached game backend.
        :param boat_type: Type of boat {'small', 'medium', 'large'}
        """

        self.base_sim = sim
        self.game_handle = game

        # Call the parent init.
        super().__init__(self.IMAGES[boat_type], self.game_handle.sprite_scaling)

        # Retrieve boat length from constants above.
        self.length = self.SPRITE_LENGTHS[boat_type]
        # FIXME: with new method signature
        self.vehicle_model = self.base_sim.add_boat(self.base_sim, boat_id, center_x, center_y, boat_type=boat_type)

        self.center_x = center_x
        self.center_y = center_y

        # Adding sprite for ripple effects.
        self.ripple_sprite = arcade.Sprite(
            filename=self.RIPPLES[boat_type].format(boat_type, random.randint(0, 0),
                                              center_x=center_x,
                                              center_y=center_y, hit_box_algorithm="None"))
        self.ripple_sprite.scale = self.game_handle.sprite_scaling + 0.1  # FIXME: Workaround to avoid overlap


    def ripple(self):
        """
        Returns the ripple sprite for this particular boat.
        :rtype: arcade.Sprite object
        """
        return self.ripple_sprite

    def update_ripple_sprite(self, radians, center_x, center_y):
        """
        Updates the position and rotation of the ripple sprite.
        :param radians: Angle of the ripple sprite in radians.
        :param center_x: Center X position of the ripple sprite.
        :param center_y: Center Y position of the ripple sprite.
        """
        self.ripple_sprite.radians = radians

        # Ripples need to be slightly larger than the boat sprites or they will be occluded.
        # We add the RIPPLE_OFFSET constant to adjust for that.
        self.ripple_sprite.center_x = center_x + self.RIPPLE_OFFSET * math.cos(radians)
        self.ripple_sprite.center_y = center_y + self.RIPPLE_OFFSET * math.sin(radians)
        self.ripple_sprite.alpha = math.fabs(self.vehicle_model.relative_speed() * 255)

        self.ripple_sprite.update()

    def update(self):
        """
        Queries the model and updates the boat sprite.
        """
        # Update vehicle physics
        self.vehicle_model.simulate_kinematics()

        # Rotate the boat
        self.radians = self.vehicle_model.heading

        # Find our change based on our speed and angle
        self.center_x, self.center_y = self.vehicle_model.get_position(self.game_handle.zoom_factor)

        self.update_ripple_sprite(self.radians, self.center_x, self.center_y)


class BoatGUI(arcade.Window):
    """
    Main application class. This is a scene of multiple boats heading towards each other
    and attempting to avoid collisions using the methods described in the paper.
    To run scenarios, we expect to be fed a config file with details of the simulation.
    Examples are provided in the scenarios folder.
    """
    SIZES = {"small": 105, "medium": 179, "large": 368}

    def __init__(self, config_file_path):
        """
        Reads the config file and initialises the interface.
        """
        # Variable containing the general config dict.
        self.all_configs = None
        with open(config_file_path) as file:
            self.all_configs = json.load(file)

        # Separate the graphics part from the general config.
        graphics_config = self.all_configs["sim"]["graphics"]

        # Load some properties.
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
        self.screenshot_counter = 0

        # Call the parent class initializer.
        super().__init__(width, height, title, resizable=True)

        # Set the working directory (where we expect to find files) to the same
        # directory this .py file is in.
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        # Base simulator (headless) that is common to all agents.
        self.base_sim = Sim(sim_config=self.all_configs["sim"])

        # Gets all sprites (boats/ripples/etc) involved.
        self.all_sprite_list = arcade.SpriteList()

        # Boat sprites exclusively.
        self.boat_sprites = []

        # Set the background color
        arcade.set_background_color(arcade.color.BLACK)

        # Load optional render config
        self.draw_potential_field = graphics_config["potential_field"]["render"]
        self.potential_field_resolution = graphics_config["potential_field"]["resolution"]
        self.draw_goals = graphics_config["goals"]
        self.draw_avoidance_boundaries = graphics_config["avoidance_boundaries"]
        self.draw_desired_heading = graphics_config["desired_heading"]
        self.draw_names = graphics_config["names"]
        self.draw_trajectories = graphics_config["trajectories"]
        self.debug = graphics_config["debug_info"]

        # Background textures where boats will be drawn on.
        self.background_textures = []

        self.timestamp = time.time()
        self.frame_counter = 0

    def load_background_textures(self):
        """
        Loads background textures and creates an animation loop by cycling over them.
        """
        background_config = self.all_configs["sim"]["graphics"]["background"]
        background_path = background_config["path"]
        frames = background_config["frames"]
        for i in range(1, frames):
            if i % 100 == 0:
                print("{}%".format(100*i/frames))
            texture = arcade.load_texture(background_path+"scene{:05d}.png".format(i))
            self.background_textures.append(texture)

    def load_boats(self):
        """
        Creates BoatSprites from the boat specification in the config file.
        """
        boats = self.all_configs["sim"]["boats"]
        boat_id = 0
        for boat in boats:
            boat_sprite = BoatSprite(self, boat_id, boat["start_x"], boat["start_y"], self.base_sim, boat["size"])
            boat_sprite.vehicle_model.set_goal(boat["goal_x"], boat["goal_y"])
            boat_sprite.vehicle_model.name = boat["name"]
            boat_sprite.vehicle_model.heading = math.radians(boat["initial_heading"])
            boat_sprite.vehicle_model.goal_colour = boat["colour"]
            boat_sprite.vehicle_model.write_trajectories = self.all_configs["sim"]["write_trajectories"]
            self.boat_sprites.append(boat_sprite)
            self.all_sprite_list.extend([boat_sprite, boat_sprite.ripple()])
            boat_id += 1

    def on_draw(self):
        """
        Render the screen.
        """

        timestamp = time.time()
        self.timestamp = timestamp
        self.frame_counter += 1

        # This variable controls how much we want to slow the background loop.
        slow_factor = 3
        frame = self.frame_counter % (slow_factor * len(self.background_textures))
        self.frame_counter = frame
        frame = int(frame/slow_factor)

        # This command has to happen before we start drawing
        arcade.start_render()

        # Draw the background texture
        width = self.all_configs["sim"]["graphics"]["width"]
        height = self.all_configs["sim"]["graphics"]["height"]
        arcade.draw_lrwh_rectangle_textured(0, 0, width, height, self.background_textures[frame])

        # Draw all the sprites.
        self.all_sprite_list.draw()

        def draw_arrow(x1, y1, angle, length, colour, thickness = 1.0):
            """
            Helper function that draws an arrow from the tip of the boat, indicating desired steering.
            :param x1: X coordinate of beginning of arrow.
            :param y1: Y coordinate of beginning of arrow.
            :param angle: Angle the arrow is pointing at.
            :param length: Length of the arrow.
            :param colour: Colour of the arrow.
            :param thickness: Thickness of the arrow.
            """

            # Draw arrow body.
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

            # This controls how wide/narrow is our arrowhead.
            arrowhead_angle = math.pi / 6
            ax = udx * math.cos(arrowhead_angle) - udy * math.sin(arrowhead_angle)
            ay = udx * math.sin(arrowhead_angle) + udy * math.cos(arrowhead_angle)
            bx = udx * math.cos(arrowhead_angle) + udy * math.sin(arrowhead_angle)
            by = -udx * math.sin(arrowhead_angle) + udy * math.cos(arrowhead_angle)
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

                # Draws the trajectories of the boat as a series of dots.
                if self.draw_trajectories:
                    trajectory = boat.vehicle_model.trajectory
                    for i in range(0, len(trajectory), 30):  # Draw one in each of 30 points saved.
                        arcade.draw_point(trajectory[i][0] * self.zoom_factor, trajectory[i][1] * self.zoom_factor, colour, 3)

                # Draws the names of the boats.
                if self.draw_names:
                    name = boat.vehicle_model.name
                    text_colour = arcade.color.WHITE if colour_id == "blue" or colour_id == "red" else arcade.color.BLACK
                    # arcade.draw_text(name, goal_x, goal_y, text_colour, 15)
                    arcade.draw_text(name, boat_x, boat_y+10, colour, 17)


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
                arcade.draw_circle_outline(cx, cy, min_distance, arcade.color.LIGHT_BLUE, 0.75)
                arc_angle = math.degrees(boat.vehicle_model.heading) + 90
                arcade.draw_arc_outline(cx, cy, 2*max_distance, 2*max_distance, arcade.color.LIGHT_BLUE, 0, 180, 1, arc_angle, 30)

        # Draws the desired heading.
        if self.draw_desired_heading:
            for boat in self.boat_sprites:
                if boat.vehicle_model.at_destination:
                    continue
                cx, cy = boat.vehicle_model.get_position(self.zoom_factor)
                desired_hdg = boat.vehicle_model.DEBUG_desired_heading
                length = 40
                draw_arrow(cx, cy, desired_hdg, length, arcade.color.RED, thickness=2.0)

        # Draws some debug information.
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
        """ Overriden function called on updates.
        :param delta_time: Unused parameter from base call.
        """

        # Call update on all sprites.
        self.all_sprite_list.update()

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        if key == arcade.key.UP:
            self.up_pressed = True
        elif key == arcade.key.DOWN:
            self.down_pressed = True
        elif key == arcade.key.ENTER:
            image = arcade.draw_commands.get_image(x=0, y=0, width=1900, height=1000)
            self.screenshot_counter += 1
            image.save("screenshot{}.png".format(self.screenshot_counter), "PNG")
            print("screenshot{}.png saved!".format(self.screenshot_counter))
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

        self.load_background_textures()
        self.load_boats()


    def set_viewport(self, left: float, right: float, bottom: float, top: float):
        """
        Sets the viewport for the rendering. Used when scrolling or zooming.
        :param left, right, bottom, top: Coordinates of the viewport.
        """
        self.viewport_left, self.viewport_right, self.viewport_bottom, self.viewport_top = left, right, bottom, top
        arcade.set_viewport(left, right, bottom, top)


    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        """
        Captures mouse scrolling events and calls set_viewport to adjust the view.
        :param x, y: Position of the scroll event.
        :param scroll_x, scroll_y: Intensity of the scroll in each dimension.
        """
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
        """
        Similar to on_mouse_scroll, but capturing mouse drag events.
        :param x, y: Initial drag coordinates.
        :param dx, dy: Change in drag coordinates.
        :param buttons, modifiers: Buttons and modifiers (SHIFT, CTRL etc) captured.
        """
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


#####################################
############# SCRIPTS ###############
#####################################

# FIXME: Those scripts should be in their own file.

def run_sim(sim):
    """
    Simple simulation loop.
    :param sim: Sim instance running the headless simulation.
    """
    while sim.is_running:
        for boat in sim.boats:
            boat.simulate_kinematics()


def run_boat_experiments(config_file):
    """
    Runs boat experiments using the headless sim. Runs multiple batches of experiments
    in the shown order.
    """
    print("Loading JSON config.")
    with open(config_file) as file:
        data = json.load(file)
    print("JSON config loaded.")
    headless = data["sim"]["graphics"]["headless"]
    if not headless:
        return
    # Fixed max_g experiment. We define max_g as 40.
    max_g = 20
    # Run one normal plus one subjective experiment per strategy. One objective at the end. Total of 9 per trial.
    strategies = data['experiments']['1']['dialogue_results'].keys()
    experiments = data['experiments']
    start = time.time()
    simulations_ran = 0
    total_simulations = 100
    for experiment_id in experiments.keys():
        results_path = "results_g{}/experiment{}/".format(max_g*2, experiment_id)
        if not os.path.exists(results_path):
            os.makedirs(results_path)
        boats_dict = experiments[experiment_id]['boats']
        dialogue_results = experiments[experiment_id]
        sim_start = time.time()
        for strategy in strategies:
            print("Running experiment {} with strategy {}.".format(experiment_id, strategy))
            sim = Sim(data["sim"], results_path, dialogue_results, budget=max_g, strategy=strategy)
            sim.load_boats(boats_dict)
            run_sim(sim)

            print("Running subjective experiment {} with strategy {}.".format(experiment_id, strategy))
            sim = Sim(data["sim"], results_path, dialogue_results, subjective=True, budget=max_g, strategy=strategy)
            sim.load_boats(boats_dict)
            run_sim(sim)


        print("Running objective experiment {}.".format(experiment_id))
        sim = Sim(data["sim"], results_path, dialogue_results, objective=True, budget=max_g)
        sim.load_boats(boats_dict)
        run_sim(sim)

        simulations_ran += 1

        sim_end = time.time()
        print("Simulated experiment {}.".format(experiment_id))
        iteration_time = sim_end - sim_start
        estimated_time_left = str(datetime.timedelta(seconds=iteration_time * (total_simulations - simulations_ran)))
        total_time = str(datetime.timedelta(seconds=sim_end - start))
        print("Time elapsed: {}. Total time elapsed: {}. Estimated remaining time: {}".format(
            str(datetime.timedelta(seconds=iteration_time)), total_time, estimated_time_left))


def run_varied_budgets(config_file):
    """
    This is a similar script to run_boat_experiments, except that it runs a much larger
    experiment, with one more dimension (varied privacy budgets).
    """
    with open(config_file) as file:
        data = json.load(file)
    headless = data["sim"]["graphics"]["headless"]
    num_strategies = len(data["sim"]["dialogue_results"])
    num_budgets = len(data["sim"]["dialogue_results"]["ArgStrategy.RANDOM_CHOICE_PRIVATE"])
    start = time.time()
    now = datetime.datetime.now()
    date_string = now.strftime("%d%b-%H%M")
    results_path = "results/multi_strategy-{}/".format(date_string)
    simulations_ran = 0
    total_simulations = 900
    if headless:
        boats_dict = data["sim"]["boats"]
        for strategy in data["sim"]["dialogue_results"].keys():
            # # FIXME: Temporary
            # if "RANDOM" not in strategy:
            #     continue
            path = results_path+strategy
            if not os.path.exists(path):
                os.makedirs(path)
            for budget in data["sim"]["dialogue_results"][strategy]:
                sim_start = time.time()
                simulations_ran += 1
                sim = Sim(data["sim"], path, budget=int(budget), strategy=strategy)
                sim.load_boats(boats_dict)
                frame_counter = 0
                while sim.is_running:
                    frame_counter += 1
                    # if frame_counter % 1000 == 0:
                    #     # print("Simulated {} frames.".format(frame_counter))
                    for boat in sim.boats:
                        boat.simulate_kinematics()
                sim_end = time.time()
                print("Simulated {} with budget {}.".format(strategy, budget))
                iteration_time = sim_end - sim_start
                estimated_time_left = str(datetime.timedelta(seconds=iteration_time * (total_simulations - simulations_ran)))
                total_time = str(datetime.timedelta(seconds=sim_end - start))
                print("Time elapsed: {}. Total time elapsed: {}. Estimated remaining time: {}".format(
                    str(datetime.timedelta(seconds=iteration_time)), total_time, estimated_time_left))
        end = time.time()
        print("Time elapsed: {:.2f} seconds".format(end - start))
        return results_path

    else:
        window = BoatGUI(config_file)
        window.setup()
        arcade.run()

def run(config_file):
    """ This is a simple script that runs the simulator in either headless or GUI mode."""
    with open(config_file) as file:
        data = json.load(file)
    headless = data["sim"]["graphics"]["headless"]
    start = time.time()
    if headless:
        boats_dict = data["sim"]["boats"]
        sim = Sim(data["sim"])
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
        window = BoatGUI(config_file)
        window.setup()
        arcade.run()

# Sample call of a GUI run.
run("scenarios/scenario-16-boats-19May-151120.json")

