from dataclasses import dataclass
from itertools import batched
from functools import cache
import logging
import platformdirs
import sqlite3

from .osm import Nominatim
from .trips import Trips


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


class Store:
    def __init__(self):
        path = platformdirs.user_cache_path("travel-site-generator") / "places.db"
        path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Loading places from %s", path)

        self.connection = sqlite3.connect(path)
        self.cursor = self.connection.cursor()

        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        logger.debug("Creating table if not exists")
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS places(
                osm_id TEXT PRIMARY KEY NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                country_code TEXT NOT NULL
            )
        """)

    def populate_from(self, *, trips: Trips):
        osm_ids = {
            osm_id
            for trip in trips
            for journey in trip.journeys
            for leg in journey.legs
            for osm_id in [leg.source.name, leg.destination.name]
        }

        existing_osm_ids = {
            row[0]
            for row in self.cursor.execute(
                f"SELECT osm_id FROM places WHERE osm_id IN ({','.join('?' * len(osm_ids))})",
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

        row = (osm_id, latitude, longitude, name, type, country_code)

        self.cursor.execute("INSERT INTO places VALUES (?, ?, ?, ?, ?, ?)", row)
        self.connection.commit()

    @cache
    def __getitem__(self, osm_id):
        osm_id, latitude, longitude, name, type, country_code = self.cursor.execute(
            "SELECT * FROM places WHERE osm_id = ?", (osm_id,)
        ).fetchone()

        return Place(
            osm_id=osm_id,
            latitude=latitude,
            longitude=longitude,
            name=name,
            type=type,
            country_code=country_code,
        )
