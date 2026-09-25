import colorsys
import random
from dataclasses import dataclass
from functools import cached_property

from .trips import Trip, Trips


@dataclass(frozen=True)
class Colour:
    red: float
    green: float
    blue: float

    @cached_property
    def rgb_value(self) -> list[int]:
        return [
            round(self.red * 255),
            round(self.green * 255),
            round(self.blue * 255),
        ]

    @cached_property
    def css_value(self) -> str:
        red, green, blue = self.rgb_value
        return f"rgb({red}, {green}, {blue})"

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
