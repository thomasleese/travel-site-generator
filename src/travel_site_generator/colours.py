import colorsys
from dataclasses import dataclass
import random
from functools import cached_property

from .trips import Trip, Trips


@dataclass(frozen=True)
class Colour:
    red: float
    green: float
    blue: float

    @cached_property
    def css_value(self) -> str:
        red = round(self.red * 255)
        green = round(self.green * 255)
        blue = round(self.blue * 255)
        return "rgb({}, {}, {})".format(red, green, blue)

    @classmethod
    def random(cls):
        hue = random.random()
        saturation = random.uniform(0.3, 0.7)
        value = random.uniform(0.4, 0.8)

        red, green, blue = colorsys.hsv_to_rgb(hue, saturation, value)

        return cls(red=red, green=green, blue=blue)


type Colours = dict[Trip, Colour]


def load(trips: Trips) -> Colours:
    colours = {}

    for trip in trips:
        colours[trip] = Colour.random()

    return colours
