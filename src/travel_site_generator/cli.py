import argparse
import logging
from pathlib import Path

from .places import load as load_places
from .routes import load as load_routes
from .timeline import load as load_timeline
from .trips import load as load_trips
from .writer import write_site


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", default=".", type=Path)
    parser.add_argument("--output", default="site", type=Path)
    parser.add_argument("--gmaps-api-key")

    args = parser.parse_args()

    input_path = args.input.resolve()
    output_path = args.output.resolve()

    logging.basicConfig(level=logging.DEBUG)

    places = load_places(input_path)
    trips = load_trips(input_path, places)
    routes = load_routes(trips, gmaps_api_key=args.gmaps_api_key)
    timeline = load_timeline(trips)

    write_site(trips, routes, timeline, output_path)


if __name__ == "__main__":
    main()
