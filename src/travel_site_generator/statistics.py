from dataclasses import dataclass
import logging

from .journeys import ModeOfTransport
from .routes import Routes
from .trips import Trips


logger = logging.getLogger(__name__)


@dataclass
class Statistics:
    total_distance_km_by_mode_of_transport: dict[ModeOfTransport, int]

    @staticmethod
    def from_trips(trips: Trips, routes: Routes) -> "Statistics":
        return Statistics(
            total_distance_km_by_mode_of_transport=calculate_total_distance_km_by_mode_of_transport(trips, routes)
        )


def calculate_total_distance_km_by_mode_of_transport(trips: Trips, routes: Routes) -> dict[ModeOfTransport, int]:
    values = {mode_of_transport: 0 for mode_of_transport in ModeOfTransport}

    for trip in trips:
        for journey in trip.journeys:
            for leg in journey.legs:
                key = leg.mode_of_transport
                values[key] = (values[key] + routes[leg].distance_km)

    return values


def load(trips: Trips, routes: Routes) -> Statistics:
    logger.info("Loading statistics for %i trips", len(trips))
    return Statistics.from_trips(trips, routes)
