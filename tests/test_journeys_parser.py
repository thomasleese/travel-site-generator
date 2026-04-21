from datetime import date

from travel_site_generator import journeys_parser
from travel_site_generator.journey import ModeOfTransport


def test_simple():
    string = "From heathrow on 2020-01-01 to gatwick by plane"

    journeys = journeys_parser.loads(string)

    assert len(journeys) == 1

    journey = journeys[0]
    assert len(journey.legs) == 1

    leg = journey.legs[0]
    assert leg.source.name == "heathrow"
    assert leg.source.date == date(2020, 1, 1)
    assert leg.destination.name == "gatwick"
    assert leg.destination.date == date(2020, 1, 1)
    assert leg.mode_of_transport == ModeOfTransport.PLANE


def test_newline():
    string = "From heathrow on 2020-01-01\nTo gatwick by plane"

    journeys = journeys_parser.loads(string)

    assert len(journeys) == 1

    journey = journeys[0]
    assert len(journey.legs) == 1

    leg = journey.legs[0]
    assert leg.source.name == "heathrow"
    assert leg.source.date == date(2020, 1, 1)
    assert leg.destination.name == "gatwick"
    assert leg.destination.date == date(2020, 1, 1)
    assert leg.mode_of_transport == ModeOfTransport.PLANE


def test_comments():
    string = "From heathrow on 2020-01-01 # a comment\nTo gatwick by plane"

    journeys = journeys_parser.loads(string)

    assert len(journeys) == 1

    journey = journeys[0]
    assert len(journey.legs) == 1

    leg = journey.legs[0]
    assert leg.source.name == "heathrow"
    assert leg.source.date == date(2020, 1, 1)
    assert leg.destination.name == "gatwick"
    assert leg.destination.date == date(2020, 1, 1)
    assert leg.mode_of_transport == ModeOfTransport.PLANE


def test_multiple_journies():
    string = """
    From heathrow to gatwick on 2020-01-01 by plane
    From stansted to luton on 2020-01-02 by bicycle
    """

    journeys = journeys_parser.loads(string)
    assert len(journeys) == 2

    journey = journeys[0]
    assert len(journey.legs) == 1

    leg = journey.legs[0]
    assert leg.source.name == "heathrow"
    assert leg.source.date == date(2020, 1, 1)
    assert leg.destination.name == "gatwick"
    assert leg.destination.date == date(2020, 1, 1)
    assert leg.mode_of_transport == ModeOfTransport.PLANE

    journey = journeys[1]
    assert len(journey.legs) == 1

    leg = journey.legs[0]
    assert leg.source.name == "stansted"
    assert leg.source.date == date(2020, 1, 2)
    assert leg.destination.name == "luton"
    assert leg.destination.date == date(2020, 1, 2)
    assert leg.mode_of_transport == ModeOfTransport.BICYCLE


def test_multiple_legs():
    string = """
    From heathrow on 2020-01-01 to gatwick by plane
    To stansted on 2020-01-02 by train
    """

    journeys = journeys_parser.loads(string)
    assert len(journeys) == 1

    journey = journeys[0]
    assert len(journey.legs) == 2

    leg = journey.legs[0]
    assert leg.source.name == "heathrow"
    assert leg.source.date == date(2020, 1, 1)
    assert leg.destination.name == "gatwick"
    assert leg.destination.date == date(2020, 1, 1)
    assert leg.mode_of_transport == ModeOfTransport.PLANE

    leg = journey.legs[1]
    assert leg.source.name == "gatwick"
    assert leg.source.date == date(2020, 1, 1)
    assert leg.destination.name == "stansted"
    assert leg.destination.date == date(2020, 1, 2)
    assert leg.mode_of_transport == ModeOfTransport.TRAIN
