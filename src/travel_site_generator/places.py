from dataclasses import dataclass
import datetime
from itertools import batched
from functools import cache
import logging
import pathlib
from zoneinfo import ZoneInfo

import tzfpy
import yaml

from .cache import SQLiteCache
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

    def get_tzinfo(self) -> ZoneInfo:
        tz = tzfpy.get_tz(self.longitude, self.latitude)
        return ZoneInfo(tz)


type Places = dict[str, Place]


class Cache(SQLiteCache):
    def __init__(self):
        super().__init__(name="places")

    def set_up_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS places(
                osm_id TEXT PRIMARY KEY NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                country_code TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
        """)

    def populate_from(self, *, osm_ids: set[str]):
        existing_osm_ids = {
            row[0]
            for row in self.cursor.execute(
                f"SELECT osm_id FROM places WHERE expires_at > CURRENT_TIMESTAMP AND osm_id IN ({','.join('?' * len(osm_ids))})",
                list(osm_ids),
            ).fetchall()
        }

        if new_osm_ids := osm_ids - existing_osm_ids:
            self.insert_osm_ids(new_osm_ids)

    def insert_osm_ids(self, osm_ids):
        logger.debug("Fetching and inserting %s", osm_ids)

        for batch in batched(osm_ids, 50):
            self._fetch_and_insert(batch)

    def _fetch_and_insert(self, osm_ids):
        for data in nominatim.lookup(osm_ids=osm_ids):
            self._insert(data)

    def _insert(self, data):
        osm_id = data["osm_type"][0].upper() + str(data["osm_id"])
        latitude = data["lat"]
        longitude = data["lon"]
        name = data["name"]
        type = data["type"]
        country_code = data["address"]["country_code"]
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            days=21
        )

        values = (osm_id, latitude, longitude, name, type, country_code, expires_at)

        self.cursor.execute("INSERT INTO places VALUES (?, ?, ?, ?, ?, ?, ?)", values)
        self.connection.commit()

    @cache
    def __getitem__(self, osm_id):
        osm_id, latitude, longitude, name, type, country_code, *_ = self.cursor.execute(
            "SELECT * FROM places WHERE expires_at > CURRENT_TIMESTAMP AND osm_id = ?",
            (osm_id,),
        ).fetchone()

        return Place(
            osm_id=osm_id,
            latitude=latitude,
            longitude=longitude,
            name=name,
            type=type,
            country_code=country_code,
        )


def load(path: pathlib.Path) -> Places:
    places_path = path / "places.yaml"

    logger.info("Loading places from %s", places_path)

    with open(places_path) as file:
        data = yaml.safe_load(file.read())

    cache = Cache()
    cache.populate_from(osm_ids=set(data.values()))
    return {slug: cache[osm_id] for slug, osm_id in data.items()}
