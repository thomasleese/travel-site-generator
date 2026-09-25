import uuid
from datetime import date

from travel_site_generator.countries import load as load_countries
from travel_site_generator.journeys import Journey, JourneyLeg, ModeOfTransport, Stop
from travel_site_generator.places import Place
from travel_site_generator.trips import Trip


def place(country_code: str):
    return Place(
        osm_id="", latitude=0, longitude=0, name="", type="", country_code=country_code
    )


def stop(country_code: str, day: int = 1) -> Stop:
    return Stop(place=place(country_code), date=date(2020, 1, day))


def leg(
    origin_country_code: str,
    destination_country_code: str,
    mode_of_transport: ModeOfTransport = ModeOfTransport.PLANE,
) -> JourneyLeg:
    return JourneyLeg(
        origin=stop(origin_country_code),
        destination=stop(destination_country_code),
        mode_of_transport=mode_of_transport,
    )


def trip(*journeys: Journey):
    return Trip(uuid=uuid.uuid4(), journeys=list(journeys), description="")


def test_single_leg():
    trips = [trip(Journey(legs=[leg("gb", "fr")]))]

    countries = load_countries(trips)

    assert countries == {"gb", "fr"}


def test_multiple_legs_share_countries():
    trips = [
        trip(Journey(legs=[leg("gb", "fr"), leg("fr", "es", ModeOfTransport.TRAIN)]))
    ]

    countries = load_countries(trips)

    assert countries == {"gb", "fr", "es"}


def test_multiple_trips_share_countries():
    trips = [
        trip(Journey(legs=[leg("gb", "fr")])),
        trip(Journey(legs=[leg("fr", "de")])),
    ]

    countries = load_countries(trips)

    assert countries == {"gb", "fr", "de"}
