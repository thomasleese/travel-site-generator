from dataclasses import dataclass
import datetime
from itertools import batched
from functools import cached_property
import logging
import pathlib
from zoneinfo import ZoneInfo

from cachetout import Cache
import tzfpy
import yaml

from .osm import Nominatim


logger = logging.getLogger(__name__)
nominatim = Nominatim()


type OpenStreetMapIdentifier = str


@dataclass(frozen=True)
class Place:
    osm_id: str

    latitude: float
    longitude: float

    name: str
    type: str
    country_code: str

    def __str__(self):
        return f"{self.name} ({self.type}, {self.country_code})"

    @cached_property
    def tzinfo(self) -> ZoneInfo:
        tz = tzfpy.get_tz(self.longitude, self.latitude)
        return ZoneInfo(tz)

    @cached_property
    def coordinates(self) -> tuple[float, float]:
        return (self.latitude, self.longitude)


type Places = dict[str, Place]


def populate_cache(cache: Cache, osm_ids: set[str]):
    existing_osm_ids = {
        osm_id for osm_id in osm_ids if cache.get(osm_id, type=Place) is not None
    }

    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        days=21
    )

    if new_osm_ids := osm_ids - existing_osm_ids:
        for batch in batched(new_osm_ids, 50):
            for data in nominatim.lookup(osm_ids=batch):
                osm_id = data["osm_type"][0].upper() + str(data["osm_id"])
                latitude = float(data["lat"])
                longitude = float(data["lon"])
                name = data["name"]
                type = data["type"]
                country_code = data["address"]["country_code"]

                place = Place(osm_id, latitude, longitude, name, type, country_code)
                cache.set(osm_id, place, expires_at=expires_at)


def load(path: pathlib.Path) -> Places:
    places_path = path / "places.yaml"

    logger.info("Loading places from %s", places_path)

    with open(places_path) as file:
        data = yaml.safe_load(file.read())

    cache = Cache("places", app_name="travel-site-generator")
    populate_cache(cache, osm_ids=set(data.values()))

    return {slug: cache.get(osm_id, type=Place) for slug, osm_id in data.items()}
