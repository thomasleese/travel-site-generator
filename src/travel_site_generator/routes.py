from dataclasses import dataclass
import logging

from .journeys import JourneyLeg


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Point:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Route:
    points: list[Point]


type Routes = dict[JourneyLeg, Route]


def load(places, trips) -> Routes:
    logger.info("Loading routes")

    routes = {}

    for trip in trips:
        for journey in trip.journeys:
            for leg in journey.legs:
                points = [
                    Point(places[slug].latitude, places[slug].longitude)
                    for slug in [leg.source.name, leg.destination.name]
                ]

                logger.debug("Loading: %s", leg)

                routes[leg] = Route(points=points)

    return routes
