import logging

from .trips import Trips

logger = logging.getLogger(__name__)

type Countries = set[str]


def load(trips: Trips) -> Countries:
    logger.info("Loading countries for %i trips", len(trips))

    return {
        stop.place.country_code
        for trip in trips
        for journey in trip.journeys
        for leg in journey.legs
        for stop in (leg.origin, leg.destination)
    }
