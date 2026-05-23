import datetime
import json
import logging
import shutil
from pathlib import Path
from typing import Any

import jinja2
from markupsafe import Markup
from mistune.util import escape as escape_text
from mistune import HTMLRenderer as BaseHTTPRenderer, Markdown

from .colours import Colours
from .routes import Routes
from .statistics import Statistics
from .timeline import Timeline
from .trips import Trips


logger = logging.getLogger(__name__)


def write_static(dst_path: Path):
    logger.info("Copying static files to %s", dst_path)
    dst_path.mkdir(parents=True, exist_ok=True)
    src_path = Path(__file__).parent.resolve() / "static"
    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)


def write_geojson(trips: Trips, colours: Colours, routes: Routes, path: Path):
    logger.info("Saving GeoJSON data to %s", path)

    features = [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [point.longitude, point.latitude]
                    for leg in journey.legs
                    for point in routes[leg].points
                ],
            },
            "style": {
                "stroke": colours[trip].css_value,
                "stroke-width": "3",
            },
        }
        for trip in trips
        for journey in trip.journeys
    ]

    data = {"type": "FeatureCollection", "features": features}

    with open(path, "w") as file:
        file.write(json.dumps(data))


class HTMLRenderer(BaseHTTPRenderer):
    def heading(self, text: str, level: int, **attrs: Any) -> str:
        tag = "h" + str(level + 1)
        html = "<" + tag
        _id = attrs.get("id")
        if _id:
            html += ' id="' + escape_text(_id) + '"'
        return html + ">" + text + "</" + tag + ">\n"


def write_index_html(
    trips: Trips,
    routes: Routes,
    timeline: Timeline,
    statistics: Statistics,
    path: Path,
):
    template_loader = jinja2.PackageLoader("travel_site_generator")

    env = jinja2.Environment(
        loader=template_loader,
        autoescape=jinja2.select_autoescape(),
    )

    markdown = Markdown(renderer=HTMLRenderer(escape=False))

    def to_date(origin: datetime.date, destination: datetime.date) -> str:
        if origin == destination:
            return origin.strftime("%-d %B %Y")

        destination_str = destination.strftime("%-d %B %Y")

        if origin.month == destination.month and origin.year == destination.year:
            origin_str = origin.strftime("%-d")
        elif origin.year == destination.year:
            origin_str = origin.strftime("%-d %B")
        else:
            origin_str = origin.strftime("%-d %B %Y")

        return f"{origin_str} – {destination_str}"

    env.filters["to_date"] = to_date
    env.filters["markdown"] = lambda value: Markup(markdown(value))

    template = env.get_template("index.html")

    index_html = template.render(
        routes=routes,
        statistics=statistics,
        timeline=timeline,
        trips=trips,
    )

    with open(path, "w") as file:
        file.write(index_html)


def generate(
    trips: Trips,
    colours: Colours,
    routes: Routes,
    timeline: Timeline,
    statistics: Statistics,
    path: Path,
):
    logger.info("Saving to %s", path)

    path.mkdir(parents=True, exist_ok=True)

    write_static(path / "static")
    write_index_html(trips, routes, timeline, statistics, path / "index.html")
    write_geojson(trips, colours, routes, path / "data.json")
