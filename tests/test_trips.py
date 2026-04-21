import io

from travel_site_generator.trips import _load as load_trip


def test_single():
    # TODO: Switch to de-indented strings.
    string = """
===
From heathrow on 2020-01-01 to gatwick by plane
===

# London
"""

    trip = load_trip(io.StringIO(string))

    assert len(trip.journeys) == 1
    assert trip.description == "# London"


def test_multiple():
    # TODO: Switch to de-indented strings.
    string = """
===
From heathrow on 2020-01-01 to gatwick by plane

From gatwick on 2020-01-02 to heathrow by train
===

# London
"""

    trip = load_trip(io.StringIO(string))

    assert len(trip.journeys) == 2
    assert trip.description == "# London"
