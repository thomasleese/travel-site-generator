import json
import logging
from pathlib import Path

import jinja2
from markupsafe import Markup
import mistune

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


def generate(trips: Trips, routes: Routes, timeline: Timeline, path: Path):
    logger.info("Saving to %s", path)

    path.mkdir(parents=True, exist_ok=True)

    write_geojson(trips, routes, path / "data.json")

    env = jinja2.Environment(
        loader=jinja2.PackageLoader("travel_site_generator", "templates"),
        autoescape=jinja2.select_autoescape(),
    )

    def markdown(value):
        return Markup(mistune.markdown(value))

    env.filters["markdown"] = markdown

    template = env.get_template("index.html")

    index_html = template.render(trips=trips, routes=routes, timeline=timeline)

    with open(path / "index.html", "w") as file:
        file.write(index_html)
