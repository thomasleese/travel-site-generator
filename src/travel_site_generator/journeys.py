import datetime
from dataclasses import dataclass

import joml

from .mode_of_transport import ModeOfTransport
from .places import Place, Places


@dataclass(frozen=True)
class Stop:
    place: Place
    date: datetime.date

    def __str__(self):
        return f"{self.place} ({self.date})"

    def __lt__(self, other):
        if not isinstance(other, Stop):
            return NotImplemented
        return self.date < other.date


@dataclass(frozen=True)
class Leg:
    origin: Stop
    destination: Stop
    mode_of_transport: ModeOfTransport

    def __str__(self):
        return f"{self.origin} to {self.destination} by {self.mode_of_transport}"


@dataclass(frozen=True)
class Journey:
    legs: list[Leg]

    def __lt__(self, other):
        if not isinstance(other, Journey):
            return NotImplemented
        return self.origin < other.origin

    @property
    def origin(self) -> Stop:
        return self.legs[0].origin

    @property
    def destination(self) -> Stop:
        return self.legs[-1].destination


type Journeys = list[Journey]


def parsed_stop_to_stop(parsed_stop: joml.Stop, places: Places) -> Stop:
    return Stop(places[parsed_stop.place_name], parsed_stop.date)


def parsed_leg_to_leg(parsed_leg: joml.Leg, places: Places) -> Leg:
    return Leg(
        origin=parsed_stop_to_stop(parsed_leg.origin, places),
        destination=parsed_stop_to_stop(parsed_leg.destination, places),
        mode_of_transport=ModeOfTransport(parsed_leg.mode_of_transport),
    )


def parsed_journey_to_journey(parsed_journey: joml.Journey, places: Places) -> Journey:
    return Journey(legs=[parsed_leg_to_leg(leg, places) for leg in parsed_journey.legs])


def load(string: str, places: Places) -> Journeys:
    parsed_journeys = joml.loads(string)

    journeys = [
        parsed_journey_to_journey(parsed_journey, places)
        for parsed_journey in parsed_journeys
    ]

    return sorted(journeys)
