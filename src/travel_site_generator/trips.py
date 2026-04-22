from dataclasses import dataclass
import io
import logging
import pathlib
import re

import frontmatter
from frontmatter.default_handlers import BaseHandler

from .journeys import load as load_journeys, Journeys, Journey
from .places import Places


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Trip:
    journeys: Journeys
    description: str

    @property
    def origin(self) -> Journey:
        return self.journeys[0]

    @property
    def destination(self) -> Journey:
        return self.journeys[-1]

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Trip):
            return NotImplemented
        return self.origin < other.origin


type Trips = list[Trip]


class JourneysHandler(BaseHandler):
    FM_BOUNDARY = re.compile(r"^={3,}\s*$", re.MULTILINE)
    START_DELIMITER = END_DELIMITER = "==="

    def __init__(self, places: Places, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)
        self.places = places

    def load(self, fm: str, **kwargs: object) -> dict[str, Journeys]:
        return {"journeys": load_journeys(fm, self.places)}


def _load(fd: str | io.IOBase | pathlib.Path, places: Places) -> Trip:
    post = frontmatter.load(fd, handler=JourneysHandler(places))
    return Trip(journeys=post["journeys"], description=post.content)


def load(path: pathlib.Path, places: Places) -> Trips:
    logger.info("Loading trips from %s", path)

    trips = []

    for trip_path in sorted((path / "trips").glob("*/*.md")):
        name = str(trip_path)[len(str(path)) + 7 :]
        logger.info("Loading %s", name)
        trips.append(_load(trip_path, places))

    return sorted(trips)
