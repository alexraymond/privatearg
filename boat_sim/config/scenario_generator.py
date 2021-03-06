import json
import random
import math
from datetime import datetime

graphics_settings = """
    {
      "headless" : true,
      "window_title": "Boat Sim",
      "width" : 1900,
      "height" : 900,
      "sprite_scaling": 0.25,
      "zoom_factor": 0.5,
      "background":
      {
        "path": "images/background_frames2/",
        "frames": 30
      },
      "potential_field":
      {
        "render" : false,
        "resolution" : 30
      },
      "goals": true,
      "avoidance_boundaries": true,
      "desired_heading": true,
      "names": true,
      "debug_info": false
    } 
    """

names_string = """
Angel
Syracuse
Wisdom
Halo
Resolution
USS Ulysses
HWSS Traveller
SSE Harbinger
BS Vigilant
ISS Intervention
Victory
Suzanna
Triumph
Wailing Wind
Vespira
SC Scorpio
LWSS Triumph
SC Aries
USS Destroyer
USS The Trident
Duke
Titan
Tyrant
Flavia
Legacy
USS Thor
CS Spectator
USS Crash
SC Pandora
BS Vengeance
Archmage
Neurotoxin
Malta
Destiny
Valhalla
STS Vulture
STS Victoria
CS Cyclops
HWSS Wellington
HWSS Tennessee
Star Talon
Flavia
Alto
Leviathan
The Spectator
BS Nomad
HMS Malevolent
BC Pontiac
SSE Janissary
STS Tennessee
"""

def generate_multi_scenario(filename = '../experiment_data.json'):
    graphics = json.loads(graphics_settings)
    scenario = {"sim": {}}
    scenario["sim"]["graphics"] = graphics
    scenario["sim"]["avoidance_min_distance"] = 100
    scenario["sim"]["avoidance_max_distance"] = 1000
    scenario["sim"]["write_trajectories"] = True
    scenario["experiments"] = {}
    height = graphics["height"] / graphics["zoom_factor"]
    width = graphics["width"] / graphics["zoom_factor"]
    with open(filename, 'r') as file:
        overall_data = json.load(file)
    for experiment_id in overall_data.keys():
        print("Generating scenario for experiment {}...".format(experiment_id))
        experiment_data = overall_data[experiment_id]
        current_scenario = scenario["experiments"][experiment_id] = {}
        num_boats = experiment_data["num_agents"]
        horizontal_separation = 1100
        max_width = horizontal_separation * num_boats  # Added width so initial scene is empty.
        boat_names = names_string.split('\n')
        boats = []
        positions = range(int(-max_width / 2), int(max_width / 2 + width), horizontal_separation)
        positions = [p for p in positions if p < 0 or p > width]
        for i in range(len(positions)):
            boat = {"name": random.choice(boat_names)}
            size_probabilities = {"small": 1.0,
                                  "medium": 0.0,
                                  "large": 0.00}
            size = random.choices(list(size_probabilities.keys()), list(size_probabilities.values()), k=1)[0]
            boat["size"] = size
            boat["id"] = i
            boat["start_x"] = positions[i]
            boat["start_y"] = random.randint(height * 0.4, height * 0.6)
            boat["goal_x"] = positions[-i - 1]
            boat["goal_y"] = random.randint(height * 0.4, height * 0.6)
            heading_to_target = math.atan2(boat["goal_y"] - boat["start_y"], boat["goal_x"] - boat["start_x"]) + math.pi
            boat["initial_heading"] = math.degrees(heading_to_target)
            boat["colour"] = random.choice(["red", "green", "blue", "yellow"])
            boats.append(boat)
        current_scenario["boats"] = boats
        current_scenario["dialogue_results"] = experiment_data["results"]["per_strategy"]
        current_scenario["ground_truth"] = experiment_data["ground_truth"]
        now = datetime.now()
        date_string = now.strftime("%d%b-%H%M%S")
        filename = "scenarios/multi_scenarios/scenario-{}-boats-{}.json".format(num_boats, experiment_id)
    print("Saving to JSON...")
    with open(filename, 'w') as file:
        json.dump(scenario, file, indent=4)
    return filename

def generate_scenario(filename = '../experiment_data.json'):
    graphics = json.loads(graphics_settings)
    scenario = {"sim": {}}
    scenario["sim"]["graphics"] = graphics
    scenario["sim"]["avoidance_min_distance"] = 100
    scenario["sim"]["avoidance_max_distance"] = 1000
    scenario["sim"]["write_trajectories"] = True
    height = graphics["height"] / graphics["zoom_factor"]
    width = graphics["width"] / graphics["zoom_factor"]
    with open(filename, 'r') as file:
        experiment_data = json.load(file)
    num_boats = experiment_data["num_agents"]
    horizontal_separation = 1000
    max_width = horizontal_separation * num_boats  # Added width so initial scene is empty.
    boat_names = names_string.split('\n')
    boats = []
    positions = range(int(-max_width / 2), int(max_width / 2 + width), horizontal_separation)
    positions = [p for p in positions if p < 0 or p > width]
    for i in range(len(positions)):
        boat = {"name": random.choice(boat_names)}
        size_probabilities = {"small": 1.0,
                              "medium": 0.0,
                              "large": 0.00}
        size = random.choices(list(size_probabilities.keys()), list(size_probabilities.values()), k=1)[0]
        boat["size"] = size
        boat["id"] = i
        boat["start_x"] = positions[i]
        boat["start_y"] = random.randint(height * 0.4, height * 0.6)
        boat["goal_x"] = positions[-i - 1]
        boat["goal_y"] = random.randint(height * 0.4, height * 0.6)
        heading_to_target = math.atan2(boat["goal_y"] - boat["start_y"], boat["goal_x"] - boat["start_x"]) + math.pi
        boat["initial_heading"] = math.degrees(heading_to_target)
        boat["colour"] = random.choice(["red", "green", "blue", "yellow"])
        boats.append(boat)
    scenario["sim"]["boats"] = boats
    scenario["sim"]["dialogue_results"] = experiment_data["results"]["per_strategy"]
    now = datetime.now()
    date_string = now.strftime("%d%b-%H%M%S")
    filename = "scenarios/scenario-and-dialogue-{}-boats-{}.json".format(num_boats, date_string)
    with open(filename, 'w') as file:
        json.dump(scenario, file, indent=4)
    return filename

def generate_random_scenario(num_boats):
    graphics = json.loads(graphics_settings)
    experiment_data = {}
    with open('../../experiment_data.json', 'r') as file:
        experiment_data = json.load(file)
    scenario = {"sim": {}}
    scenario["sim"]["graphics"] = graphics
    scenario["sim"]["avoidance_min_distance"] = 100
    scenario["sim"]["avoidance_max_distance"] = 1000
    scenario["sim"]["write_trajectories"] = True
    height = graphics["height"] / graphics["zoom_factor"]
    width = graphics["width"] / graphics["zoom_factor"]
    horizontal_separation = 1000
    max_width = horizontal_separation * num_boats  # Added width so initial scene is empty.
    boat_names = names_string.split('\n')
    boats = []
    positions = range(int(-max_width/2), int(max_width/2 + width), horizontal_separation)
    positions = [p for p in positions if p < 0 or p > width]
    for i in range(len(positions)):
        boat = {"name": random.choice(boat_names)}
        size_probabilities = {"small": 1.0,
                              "medium": 0.0,
                              "large": 0.00}
        size = random.choices(list(size_probabilities.keys()), list(size_probabilities.values()), k=1)[0]
        boat["size"] = size
        boat["start_x"] = positions[i]
        boat["start_y"] = random.randint(height*0.4, height*0.6)
        boat["goal_x"] = positions[-i-1]
        boat["goal_y"] = random.randint(height*0.4, height*0.6)
        heading_to_target = math.atan2(boat["goal_y"] - boat["start_y"], boat["goal_x"] - boat["start_x"]) + math.pi
        boat["initial_heading"] = math.degrees(heading_to_target)
        boat["colour"] = random.choice(["red", "green", "blue", "yellow"])
        boats.append(boat)
    random.shuffle(boats)
    scenario["sim"]["boats"] = boats
    now = datetime.now()
    date_string = now.strftime("%d%b-%H%M%S")
    filename = "scenarios/scenario-{}-boats-{}.json".format(num_boats, date_string)
    with open(filename, 'w') as file:
        json.dump(scenario, file, indent=4)
    return filename

