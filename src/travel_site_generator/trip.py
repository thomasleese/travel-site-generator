from dataclasses import dataclass

from .journey import Journey


@dataclass(frozen=True)
class Trip:
    journeys: list[Journey]
    description: str
