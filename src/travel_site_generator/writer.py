import json
import logging
from pathlib import Path

from .routes import Routes
from .timeline import Timeline
from .trips import Trips


logger = logging.getLogger(__name__)


def write_geojson(trips: Trips, routes: Routes, path: Path):
    logger.info("Saving GeoJSON data to %s", path)

    features = [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "coordinates": [
                    [point.longitude, point.latitude]
                    for leg in journey.legs
                    for point in routes[leg].points
                ],
                "type": "LineString",
            },
        }
        for trip in trips
        for journey in trip.journeys
    ]

    data = {"type": "FeatureCollection", "features": features}

    with open(path, "w") as file:
        file.write(json.dumps(data))


def write_site(trips: Trips, routes: Routes, timeline: Timeline, path: Path):
    logger.info("Saving to %s", path)

    path.mkdir(parents=True, exist_ok=True)

    write_geojson(trips, routes, path / "data.json")
