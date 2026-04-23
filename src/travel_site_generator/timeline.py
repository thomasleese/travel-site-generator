import datetime
from dataclasses import dataclass
import logging
from typing import Optional

from .journeys import Journey, Stop, ModeOfTransport, JourneyLeg
from .places import Place
from .routes import Routes
from .trips import Trip, Trips


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TimelineEntry:
    place: Optional[Place] = None
    origin_date: Optional[datetime.date] = None
    destination_date: Optional[datetime.date] = None
    mode_of_transport: Optional[ModeOfTransport] = None
    distance_km: Optional[int] = None

    @staticmethod
    def from_stop(stop: Stop) -> TimelineEntry:
        return TimelineEntry(place=stop.place)

    @staticmethod
    def from_leg(leg: JourneyLeg, routes: Routes) -> TimelineEntry:
        return TimelineEntry(
            origin_date=leg.origin.date,
            destination_date=leg.destination.date,
            mode_of_transport=leg.mode_of_transport,
            distance_km=routes[leg].distance_km,
        )


@dataclass(frozen=True)
class TimelineJourney:
    entries: list[TimelineEntry]

    @staticmethod
    def from_journey(journey: Journey, routes: Routes) -> TimelineJourney:
        entries = [TimelineEntry.from_stop(journey.origin)]

        for leg in journey.legs:
            entries.append(TimelineEntry.from_leg(leg, routes))
            entries.append(TimelineEntry.from_stop(leg.destination))

        return TimelineJourney(entries=entries)


@dataclass(frozen=True)
class TimelineTrip:
    description: str
    journeys: list[TimelineJourney]

    @staticmethod
    def from_trip(trip: Trip, routes: Routes) -> TimelineTrip:
        return TimelineTrip(
            description=trip.description,
            journeys=[
                TimelineJourney.from_journey(journey, routes)
                for journey in trip.journeys
            ],
        )


@dataclass(frozen=True)
class Timeline:
    trips: list[TimelineTrip]

    @staticmethod
    def from_trips(trips: Trips, routes: Routes) -> Timeline:
        return Timeline(
            trips=list(
                reversed([TimelineTrip.from_trip(trip, routes) for trip in trips])
            )
        )


def load(trips: Trips, routes: Routes) -> Timeline:
    logger.info("Loading timeline from %i trips", len(trips))
    return Timeline.from_trips(trips, routes)
