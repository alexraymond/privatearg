from vehicle_model import BoatModel

class Sim:
    """
    Main class for computing simulations and game logic in a headless manner.
    """

    def __init__(self):
        self.vehicles = []

    def add_boat(self, x, y, length):
        boat = BoatModel(center_x=x, center_y=y, length=length)
        self.vehicles.append(boat)
        return boat
