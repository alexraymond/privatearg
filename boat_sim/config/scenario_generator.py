import json
import random
from datetime import datetime

graphics_settings = """
    {
      "headless" : false,
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
HWSS The Traveler
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
The Titan
Tyrant
Flavia
Legacy
USS Thor
CS The Spectator
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
CS Cyclopse
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



def generate_scenario(num_boats):
    graphics = json.loads(graphics_settings)
    scenario = {"sim": {}}
    scenario["sim"]["graphics"] = graphics
    height = graphics["height"] / graphics["zoom_factor"]
    width = graphics["width"] / graphics["zoom_factor"]
    horizontal_separation = 400
    max_width = horizontal_separation * num_boats  # Added width so initial scene is empty.
    boat_names = names_string.split('\n')
    boats = []
    positions = range(int(-max_width/2), int(max_width/2 + width), horizontal_separation)
    positions = [p for p in positions if p < 0 or p > width]
    for i in range(len(positions)):
        boat = {"name": random.choice(boat_names)}
        size_probabilities = {"small": 0.6,
                              "medium": 0.35,
                              "large": 0.05}
        size = random.choices(list(size_probabilities.keys()), list(size_probabilities.values()), k=1)[0]
        boat["size"] = size
        boat["start_x"] = positions[i]
        boat["start_y"] = random.randint(height*0.4, height*0.6)
        boat["initial_heading"] = 180 if boat["start_x"] < 0 else 0
        boat["goal_x"] = positions[-i-1]
        boat["goal_y"] = random.randint(height*0.4, height*0.6)
        boat["colour"] = random.choice(["red", "green", "blue", "yellow"])
        boats.append(boat)
    random.shuffle(boats)
    scenario["sim"]["boats"] = boats
    now = datetime.now()
    date_string = now.strftime("%d%b-%H%M")
    filename = "scenario-{}-boats-{}.json".format(num_boats, date_string)
    with open(filename, 'w') as file:
        json.dump(scenario, file, indent=4)

generate_scenario(30)
