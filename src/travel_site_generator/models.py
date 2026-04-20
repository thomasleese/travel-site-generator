from datetime import date

from pydantic import BaseModel, Field


type OpenStreetMapIdentifier = str


class Journey(BaseModel):
    dates: list[date] = Field(frozen=True)
    stops: list[OpenStreetMapIdentifier] = Field(frozen=True)


class Trip(BaseModel):
    name: str = Field(frozen=True)
    journeys: list[Journey] = Field(frozen=True)


class Journal(BaseModel):
    trips: list[Trip] = Field(frozen=True)


class Place(BaseModel):
    osm_id: str = Field(frozen=True)

    latitude: float = Field(frozen=True)
    longitude: float = Field(frozen=True)

    name: str = Field(frozen=True)
    type: str = Field(frozen=True)
