import datetime
import logging
from dataclasses import dataclass

from .colours import Colour, Colours
from .journeys import Journey, JourneyLeg, ModeOfTransport, Stop
from .places import Place
from .routes import Routes
from .trips import Trip, Trips

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TimelineEntry:
    place: Place | None = None
    origin_date: datetime.date | None = None
    destination_date: datetime.date | None = None
    mode_of_transport: ModeOfTransport | None = None
    distance_km: int | None = None

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
    colour: Colour
    description: str
    journeys: list[TimelineJourney]

    @staticmethod
    def from_trip(trip: Trip, colours: Colours, routes: Routes) -> TimelineTrip:
        return TimelineTrip(
            colour=colours[trip],
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
    def from_trips(trips: Trips, colours: Colours, routes: Routes) -> Timeline:
        return Timeline(
            trips=list(
                reversed(
                    [TimelineTrip.from_trip(trip, colours, routes) for trip in trips]
                )
            )
        )


def load(trips: Trips, colours: Colours, routes: Routes) -> Timeline:
    logger.info("Loading timeline for %i trips", len(trips))
    return Timeline.from_trips(trips, colours, routes)
