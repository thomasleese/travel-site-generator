import datetime
from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class Stop:
    name: str
    date: datetime.date


class ModeOfTransport(StrEnum):
    BICYCLE = "bicycle"
    BUS = "bus"
    CAR = "car"
    FERRY = "ferry"
    FOOT = "foot"
    METRO = "metro"
    MOTORCYCLE = "motorcycle"
    PLANE = "plane"
    TRAIN = "train"
    TRAM = "tram"


@dataclass(frozen=True)
class JourneyLeg:
    source: Stop
    destination: Stop
    mode_of_transport: ModeOfTransport


@dataclass(frozen=True)
class Journey:
    legs: list[JourneyLeg]

    @property
    def source(self) -> Stop:
        return self.legs[0].source

    @property
    def destination(self) -> Stop:
        return self.legs[-1].destination
