from dataclasses import dataclass
import io
import logging
import pathlib
import re

import frontmatter
from frontmatter.default_handlers import BaseHandler

from .journeys import load as load_journeys, Journeys


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Trip:
    journeys: Journeys
    description: str


type Trips = list[Trip]


class JourneysHandler(BaseHandler):
    FM_BOUNDARY = re.compile(r"^={3,}\s*$", re.MULTILINE)
    START_DELIMITER = END_DELIMITER = "==="

    def load(self, fm: str, **kwargs: object) -> dict[str, Journeys]:
        return {"journeys": load_journeys(fm)}


def _load(fd: str | io.IOBase | pathlib.Path) -> Trip:
    post = frontmatter.load(fd, handler=JourneysHandler())
    return Trip(journeys=post["journeys"], description=post.content)


def load(path: pathlib.Path) -> Trips:
    trips = []

    for trip_path in (path / "trips").glob("*/*.md"):
        name = str(trip_path)[len(str(path)) + 7 :]
        logger.info("Loading %s", name)
        trips.append(_load(trip_path))

    return trips
