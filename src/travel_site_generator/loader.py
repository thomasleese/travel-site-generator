import logging
from pathlib import Path
import yaml

from .models import Journal, Trip


logger = logging.getLogger(__name__)


def load_trip(path: Path) -> Trip:
    logger.info("Loading trip from %s", path.name)

    with path.open() as file:
        data = yaml.safe_load(file)

    return Trip.model_validate(data)


def load_journal(path: Path) -> Journal:
    logger.info("Loading from %s", path)

    trips = []

    for trip_path in (path / "trips").glob("*.yaml"):
        trips.append(load_trip(trip_path))

    return Journal(trips=trips)
