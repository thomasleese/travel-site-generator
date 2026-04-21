import logging
from pathlib import Path

from .models import Journal
from . import trip_parser


logger = logging.getLogger(__name__)


def load_journal(path: Path) -> Journal:
    logger.info("Loading from %s", path)

    trips = []

    for trip_path in (path / "trips").glob("*.md"):
        logger.info("Loading trip from %s", trip_path.name)
        trips.append(trip_parser.load(trip_path))

    return Journal(trips=trips)
