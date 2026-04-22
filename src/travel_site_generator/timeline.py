import datetime
from dataclasses import dataclass
import logging
from typing import Optional

from .journeys import Journey, Stop, ModeOfTransport, JourneyLeg
from .places import Place
from .trips import Trip, Trips


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TimelineEntry:
    place: Optional[Place] = None
    origin_date: Optional[datetime.date] = None
    destination_date: Optional[datetime.date] = None
    mode_of_transport: Optional[ModeOfTransport] = None

    @staticmethod
    def from_stop(stop: Stop) -> TimelineEntry:
        return TimelineEntry(place=stop.place)

    @staticmethod
    def from_leg(leg: JourneyLeg) -> TimelineEntry:
        return TimelineEntry(
            origin_date=leg.origin.date,
            destination_date=leg.destination.date,
            mode_of_transport=leg.mode_of_transport,
        )


@dataclass(frozen=True)
class TimelineJourney:
    entries: list[TimelineEntry]

    @staticmethod
    def from_journey(journey: Journey) -> TimelineJourney:
        entries = [TimelineEntry.from_stop(journey.origin)]

        for leg in journey.legs:
            entries.append(TimelineEntry.from_leg(leg))
            entries.append(TimelineEntry.from_stop(leg.destination))

        return TimelineJourney(entries=entries)


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
        return Timeline(trips=list(reversed([TimelineTrip.from_trip(trip) for trip in trips])))


def load(trips: Trips) -> Timeline:
    logger.info("Loading timeline from %i trips", len(trips))
    return Timeline.from_trips(trips)
