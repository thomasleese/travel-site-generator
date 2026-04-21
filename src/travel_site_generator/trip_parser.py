import io
import pathlib
import re

import frontmatter
from frontmatter.default_handlers import BaseHandler

from . import journeys_parser
from .journey import Journey
from .trip import Trip


class JourneysHandler(BaseHandler):
    FM_BOUNDARY = re.compile(r"^={3,}\s*$", re.MULTILINE)
    START_DELIMITER = END_DELIMITER = "==="

    def load(self, fm: str, **kwargs: object) -> dict[str, list[Journey]]:
        return {"journeys": journeys_parser.loads(fm)}


def load(fd: str | io.IOBase | pathlib.Path) -> Trip:
    post = frontmatter.load(fd, handler=JourneysHandler())
    return Trip(journeys=post["journeys"], description=post.content)
