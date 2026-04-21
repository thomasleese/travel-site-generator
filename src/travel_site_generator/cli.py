import argparse
import logging
from pathlib import Path

from .places import Store as PlaceStore
from .trips import load as load_trips
from .writer import write_site


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", default=".", type=Path)
    parser.add_argument("--output", default="site", type=Path)

    args = parser.parse_args()

    input_path = args.input.resolve()
    output_path = args.output.resolve()

    logging.basicConfig(level=logging.DEBUG)

    places = PlaceStore()

    trips = load_trips(input_path)
    places.populate_from(trips=trips)
    write_site(trips, places, output_path)


if __name__ == "__main__":
    main()
