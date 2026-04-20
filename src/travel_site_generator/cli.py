import argparse
import logging
from pathlib import Path

from .loader import load_journal
from .places import Store as PlaceStore
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

    journal = load_journal(input_path)
    places.populate_from_journal(journal)
    write_site(journal, places, output_path)


if __name__ == "__main__":
    main()
