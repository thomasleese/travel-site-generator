from pydantic import BaseModel, Field

from .trip import Trip


type OpenStreetMapIdentifier = str


class Journal(BaseModel):
    trips: list[Trip] = Field(frozen=True)


class Place(BaseModel):
    osm_id: str = Field(frozen=True)

    latitude: float = Field(frozen=True)
    longitude: float = Field(frozen=True)

    name: str = Field(frozen=True)
    type: str = Field(frozen=True)
