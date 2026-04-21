import datetime
from dataclasses import dataclass
import logging
from typing import NamedTuple, Optional

from google.api_core.client_options import ClientOptions
from google.type.latlng_pb2 import LatLng
from google.maps import routing_v2
import polyline

from .cache import SQLiteCache
from .journeys import JourneyLeg, ModeOfTransport
from .places import Places
from .trips import Trips


logger = logging.getLogger(__name__)


class Point(NamedTuple):
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Route:
    points: list[Point]

    def to_encoded_polyline(self) -> str:
        return polyline.encode([tuple(point) for point in self.points])

    @classmethod
    def from_encoded_polyline(cls, encoded_polyline: str) -> "Route":
        points = [
            Point(latitude, longitude)
            for latitude, longitude in polyline.decode(encoded_polyline)
        ]

        return Route(points=points)


class RouteKey(NamedTuple):
    origin_latitude: float
    origin_longitude: float
    origin_date: datetime.date
    destination_latitude: float
    destination_longitude: float
    destination_date: datetime.date
    mode_of_transport: ModeOfTransport

    def to_fallback_route(self) -> Route:
        points = [
            Point(self.origin_latitude, self.origin_longitude),
            Point(self.destination_latitude, self.destination_longitude),
        ]
        return Route(points=points)

    def to_origin(self) -> routing_v2.Waypoint:
        return routing_v2.Waypoint(
            location=routing_v2.Location(
                lat_lng=LatLng(
                    latitude=self.origin_latitude,
                    longitude=self.origin_longitude,
                )
            )
        )

    def to_destination(self) -> routing_v2.Waypoint:
        return routing_v2.Waypoint(
            location=routing_v2.Location(
                lat_lng=LatLng(
                    latitude=self.destination_latitude,
                    longitude=self.destination_longitude,
                )
            )
        )

    def to_departure_time(self) -> Optional[datetime.datetime]:
        if self.mode_of_transport in [ModeOfTransport.CAR, ModeOfTransport.FOOT]:
            return None

        origin_date = (
            datetime.date.today()
        )  # FIXME: Pick a date with the same day as the journey
        origin_time = datetime.time(10)  # FIXME: This is arbitrary
        return datetime.datetime.combine(origin_date, origin_time)

    def to_arrival_time(self) -> Optional[datetime.datetime]:
        return None

    def to_travel_mode_and_transit_preferences(
        self,
    ) -> tuple[routing_v2.RouteTravelMode, Optional[routing_v2.TransitPreferences]]:
        match self.mode_of_transport:
            case ModeOfTransport.BICYCLE:
                return routing_v2.RouteTravelMode.BICYCLE, None
            case ModeOfTransport.BUS:
                return (
                    routing_v2.RouteTravelMode.TRANSIT,
                    routing_v2.TransitPreferences(
                        allowed_travel_modes=[
                            routing_v2.TransitPreferences.TransitTravelMode.BUS
                        ]
                    ),
                )
            case ModeOfTransport.CAR:
                return routing_v2.RouteTravelMode.DRIVE, None
            case ModeOfTransport.FERRY:
                return routing_v2.RouteTravelMode.TRANSIT, None
            case ModeOfTransport.FOOT:
                return routing_v2.RouteTravelMode.WALK, None
            case ModeOfTransport.METRO:
                return (
                    routing_v2.RouteTravelMode.TRANSIT,
                    routing_v2.TransitPreferences(
                        allowed_travel_modes=[
                            routing_v2.TransitPreferences.TransitTravelMode.SUBWAY
                        ]
                    ),
                )
            case ModeOfTransport.MOTORCYCLE:
                return routing_v2.RouteTravelMode.DRIVE, None
            case ModeOfTransport.TRAIN:
                return (
                    routing_v2.RouteTravelMode.TRANSIT,
                    routing_v2.TransitPreferences(
                        allowed_travel_modes=[
                            routing_v2.TransitPreferences.TransitTravelMode.TRAIN,
                            routing_v2.TransitPreferences.TransitTravelMode.RAIL,
                        ]
                    ),
                )
            case ModeOfTransport.TRAM:
                return (
                    routing_v2.RouteTravelMode.TRANSIT,
                    routing_v2.TransitPreferences(
                        allowed_travel_modes=[
                            routing_v2.TransitPreferences.TransitTravelMode.LIGHT_RAIL
                        ]
                    ),
                )
            case _:
                raise ValueError(
                    f"Unsupported mode of transport: {self.mode_of_transport}"
                )

    @classmethod
    def from_journey_leg(cls, leg: JourneyLeg, places: Places) -> "RouteKey":
        origin_place = places[leg.origin.name]
        destination_place = places[leg.destination.name]

        return cls(
            origin_latitude=origin_place.latitude,
            origin_longitude=origin_place.longitude,
            origin_date=leg.origin.date,
            destination_latitude=destination_place.latitude,
            destination_longitude=destination_place.longitude,
            destination_date=leg.destination.date,
            mode_of_transport=leg.mode_of_transport,
        )


type Routes = dict[JourneyLeg, Route]


class Cache(SQLiteCache):
    def __init__(self):
        super().__init__(name="routes")

    def set_up_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS routes(
                origin_latitude REAL NOT NULL,
                origin_longitude REAL NOT NULL,
                origin_date DATE NOT NULL,
                destination_latitude REAL NOT NULL,
                destination_longitude REAL NOT NULL,
                destination_date DATE NOT NULL,
                mode_of_transport TEXT NOT NULL,
                encoded_polyline TEXT NOT NULL
            )
        """)

    def __contains__(self, key: RouteKey) -> bool:
        return (
            self.cursor.execute(
                "SELECT 1 FROM routes WHERE origin_latitude = ? AND origin_longitude = ? AND origin_date = ? AND destination_latitude = ? AND destination_longitude = ? AND destination_date = ? AND mode_of_transport = ?",
                tuple(key),
            ).fetchone()
            is not None
        )

    def __getitem__(self, key: RouteKey) -> Route:
        result = self.cursor.execute(
            "SELECT encoded_polyline FROM routes WHERE origin_latitude = ? AND origin_longitude = ? AND origin_date = ? AND destination_latitude = ? AND destination_longitude = ? AND destination_date = ? AND mode_of_transport = ?",
            tuple(key),
        ).fetchone()

        if result is None:
            raise KeyError(f"Route not found: {key}")

        return Route.from_encoded_polyline(result[0])

    def __setitem__(self, key: RouteKey, route: Route):
        values = tuple(key) + (route.to_encoded_polyline(),)
        self.cursor.execute(
            "INSERT INTO routes VALUES (?, ?, ?, ?, ?, ?, ?, ?)", values
        )
        self.connection.commit()


class RouteFetcher:
    def __init__(self, gmaps_api_key: str):
        client_options = ClientOptions(api_key=gmaps_api_key)
        self.client = routing_v2.RoutesClient(client_options=client_options)

    def fetch(self, route_key: RouteKey) -> Route:
        origin = route_key.to_origin()
        destination = route_key.to_destination()
        departure_time = route_key.to_departure_time()
        arrival_time = route_key.to_arrival_time()
        travel_mode, transit_preferences = (
            route_key.to_travel_mode_and_transit_preferences()
        )

        request = routing_v2.ComputeRoutesRequest(
            origin=origin,
            destination=destination,
            travel_mode=travel_mode,
            departure_time=departure_time,
            arrival_time=arrival_time,
            transit_preferences=transit_preferences,
            polyline_quality=routing_v2.PolylineQuality.OVERVIEW,
        )

        response = self.client.compute_routes(
            request=request,
            metadata=[("x-goog-fieldmask", "routes.polyline.encodedPolyline")],
        )

        routes = response.routes

        if not routes:
            raise ValueError(f"No routes found for {route_key}")

        encoded_polyline = routes[0].polyline.encoded_polyline
        return Route.from_encoded_polyline(encoded_polyline)


def load(places: Places, trips: Trips, gmaps_api_key: str) -> Routes:
    logger.info("Loading routes")

    route_fetcher = RouteFetcher(gmaps_api_key)
    cache = Cache()

    routes = {}

    for trip in trips:
        for journey in trip.journeys:
            for leg in journey.legs:
                if leg in routes:
                    continue

                route_key = RouteKey.from_journey_leg(leg, places)

                if route_key.mode_of_transport == ModeOfTransport.PLANE:
                    points = [
                        Point(route_key.origin_latitude, route_key.origin_longitude),
                        Point(
                            route_key.destination_latitude,
                            route_key.destination_longitude,
                        ),
                    ]
                    routes[leg] = Route(points=points)
                    continue

                if route_key in cache:
                    routes[leg] = cache[route_key]
                    continue

                logger.info("Fetching route for %s", leg)

                try:
                    route = cache[route_key] = route_fetcher.fetch(route_key)
                except ValueError:
                    logger.warning("Failed to fetch route for %s", leg)
                    route = route_key.to_fallback_route()

                routes[leg] = route

    return routes
