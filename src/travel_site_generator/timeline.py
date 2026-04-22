import datetime
from dataclasses import dataclass
import logging
from typing import Optional

from .journeys import Journey, Stop, ModeOfTransport
from .places import Place
from .trips import Trip, Trips


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TimelineStop:
    place: Place
    date: datetime.date
    mode_of_transport: Optional[ModeOfTransport]

    @staticmethod
    def from_stop(stop: Stop, mode_of_transport: Optional[ModeOfTransport]) -> TimelineStop:
        return TimelineStop(place=stop.place, date=stop.date, mode_of_transport=mode_of_transport)


@dataclass(frozen=True)
class TimelineJourney:
    stops: list[TimelineStop]

    @staticmethod
    def from_journey(journey: Journey) -> TimelineJourney:
        stops = [TimelineStop.from_stop(journey.origin, mode_of_transport=None)]

        for leg in journey.legs:
            stops.append(TimelineStop.from_stop(leg.destination, mode_of_transport=leg.mode_of_transport))

        return TimelineJourney(stops=stops)


@dataclass(frozen=True)
class TimelineTrip:
    description: str
    journeys: list[TimelineJourney]

    @staticmethod
    def from_trip(trip: Trip) -> TimelineTrip:
        return TimelineTrip(
            description=trip.description,
            journeys=[
                TimelineJourney.from_journey(journey) for journey in trip.journeys
            ],
        )


@dataclass(frozen=True)
class Timeline:
    trips: list[TimelineTrip]

    @staticmethod
    def from_trips(trips: Trips) -> Timeline:
        return Timeline(trips=[TimelineTrip.from_trip(trip) for trip in trips])


def load(trips: Trips) -> Timeline:
    logger.info("Loading timeline from %i trips", len(trips))
    return Timeline.from_trips(trips)
