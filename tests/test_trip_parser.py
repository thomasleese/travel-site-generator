import io

from travel_site_generator import trip_parser


def test_load_single():
    # TODO: Switch to de-indented strings.
    string = """
===
From heathrow on 2020-01-01 to gatwick by plane
===

# London
"""

    trip = trip_parser.load(io.StringIO(string))

    assert len(trip.journeys) == 1
    assert trip.description == "# London"


def test_load_multiple():
    # TODO: Switch to de-indented strings.
    string = """
===
From heathrow on 2020-01-01 to gatwick by plane

From gatwick on 2020-01-02 to heathrow by train
===

# London
"""

    trip = trip_parser.load(io.StringIO(string))

    assert len(trip.journeys) == 2
    assert trip.description == "# London"
