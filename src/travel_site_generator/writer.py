import json
import logging
from pathlib import Path

from .models import Journal
from .places import Store as PlaceStore


logger = logging.getLogger(__name__)


def write_geojson(journal: Journal, places: PlaceStore, path: Path):
    logger.info("Saving GeoJSON data to %s", path)

    features = [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "coordinates": [
                    [places[osm_id].longitude, places[osm_id].latitude]
                    for leg in journey.legs
                    for osm_id in [leg.source.name, leg.destination.name]
                ],
                "type": "LineString",
            },
        }
        for trip in journal.trips
        for journey in trip.journeys
    ]

    data = {"type": "FeatureCollection", "features": features}

    with open(path, "w") as file:
        file.write(json.dumps(data))


def write_site(journal: Journal, places: PlaceStore, path: Path):
    logger.info("Saving to %s", path)

    path.mkdir(parents=True, exist_ok=True)

    write_geojson(journal, places, path / "data.json")
