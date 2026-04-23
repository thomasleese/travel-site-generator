import datetime
from dataclasses import dataclass
import logging
from typing import NamedTuple, Optional

import geopy.distance
from google.api_core.client_options import ClientOptions
from google.type.latlng_pb2 import LatLng
from google.maps import routing_v2
import polyline

from .cache import SQLiteCache
from .journeys import JourneyLeg, ModeOfTransport, Stop
from .trips import Trips


logger = logging.getLogger(__name__)


class Point(NamedTuple):
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Route:
    points: list[Point]
    distance_km: int
    is_accurate: Optional[bool] = None

    def to_encoded_polyline(self) -> str:
        return polyline.encode([tuple(point) for point in self.points])

    @classmethod
    def from_encoded_polyline(
        cls, encoded_polyline: str, distance_km: int, is_accurate: Optional[bool] = None
    ) -> "Route":
        points = [
            Point(latitude, longitude)
            for latitude, longitude in polyline.decode(encoded_polyline)
        ]

        return Route(points=points, distance_km=distance_km, is_accurate=is_accurate)


class LegWrapper:
    def __init__(self, leg: JourneyLeg):
        self.leg = leg

    @staticmethod
    def _stop_to_lat_lng(stop: Stop) -> LatLng:
        return LatLng(latitude=stop.place.latitude, longitude=stop.place.longitude)

    @classmethod
    def _stop_to_waypoint(cls, stop: Stop) -> routing_v2.Waypoint:
        return routing_v2.Waypoint(
            location=routing_v2.Location(lat_lng=cls._stop_to_lat_lng(stop))
        )

    def to_cache_values(self):
        return (
            self.leg.origin.place.latitude,
            self.leg.origin.place.longitude,
            self.leg.origin.date,
            self.leg.destination.place.latitude,
            self.leg.destination.place.longitude,
            self.leg.destination.date,
            self.leg.mode_of_transport,
        )

    def to_fallback_route(self) -> Route:
        point_a = self.leg.origin.place.coordinates
        point_b = self.leg.destination.place.coordinates

        points = [
            Point(point_a[0], point_a[1]),
            Point(point_b[0], point_b[1]),
        ]

        distance_km = round(geopy.distance.distance(point_a, point_b).km)

        return Route(points=points, distance_km=distance_km, is_accurate=False)

    def to_origin(self) -> routing_v2.Waypoint:
        return self._stop_to_waypoint(self.leg.origin)

    def to_destination(self) -> routing_v2.Waypoint:
        return self._stop_to_waypoint(self.leg.destination)

    def to_departure_time(self) -> Optional[datetime.datetime]:
        if self.leg.mode_of_transport in [ModeOfTransport.CAR, ModeOfTransport.FOOT]:
            return None

        tzinfo = self.leg.origin.place.tzinfo

        # FIXME: Pick a date with the same day as the journey
        # FIXME: Don't pick an arbitrary hour

        return datetime.datetime.now(datetime.timezone.utc).replace(
            hour=10, minute=0, second=0, tzinfo=tzinfo
        ) - datetime.timedelta(days=1)

    def to_arrival_time(self) -> Optional[datetime.datetime]:
        return None

    def to_travel_mode_and_transit_preferences(
        self,
    ) -> tuple[routing_v2.RouteTravelMode, Optional[routing_v2.TransitPreferences]]:
        match self.leg.mode_of_transport:
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
                encoded_polyline TEXT NOT NULL,
                distance_km INTEGER NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
        """)

    def __contains__(self, leg: JourneyLeg) -> bool:
        values = LegWrapper(leg).to_cache_values()

        row = self.cursor.execute(
            """
            SELECT 1 FROM routes
            WHERE origin_latitude = ?
              AND origin_longitude = ?
              AND origin_date = ?
              AND destination_latitude = ?
              AND destination_longitude = ?
              AND destination_date = ?
              AND mode_of_transport = ?
              AND expires_at > CURRENT_TIMESTAMP
        """,
            values,
        ).fetchone()

        return row is not None

    def __getitem__(self, leg: JourneyLeg) -> Route:
        values = LegWrapper(leg).to_cache_values()

        row = self.cursor.execute(
            """
            SELECT encoded_polyline, distance_km
            FROM routes
            WHERE origin_latitude = ?
              AND origin_longitude = ?
              AND origin_date = ?
              AND destination_latitude = ?
              AND destination_longitude = ?
              AND destination_date = ?
              AND mode_of_transport = ?
              AND expires_at > CURRENT_TIMESTAMP
        """,
            values,
        ).fetchone()

        if row is None:
            raise KeyError(f"Route not found: {leg}")

        return Route.from_encoded_polyline(row[0], row[1])

    def get(self, leg: JourneyLeg) -> Optional[Route]:
        try:
            return self[leg]
        except KeyError:
            return None

    def __setitem__(self, leg: JourneyLeg, route: Route):
        if route.is_accurate:
            expires_at = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(days=28)
        else:
            expires_at = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(days=7)

        values = LegWrapper(leg).to_cache_values() + (
            route.to_encoded_polyline(),
            route.distance_km,
            expires_at,
        )

        self.cursor.execute(
            "INSERT INTO routes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", values
        )
        self.connection.commit()


class RouteFetcher:
    def __init__(self, gmaps_api_key: str):
        client_options = ClientOptions(api_key=gmaps_api_key)
        self.client = routing_v2.RoutesClient(client_options=client_options)

    def fetch(self, leg: JourneyLeg) -> Route:
        leg_wrapper = LegWrapper(leg)

        origin = leg_wrapper.to_origin()
        destination = leg_wrapper.to_destination()
        departure_time = leg_wrapper.to_departure_time()
        arrival_time = leg_wrapper.to_arrival_time()
        travel_mode, transit_preferences = (
            leg_wrapper.to_travel_mode_and_transit_preferences()
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

        metadata = [
            (
                "x-goog-fieldmask",
                "routes.distanceMeters,routes.polyline.encodedPolyline",
            )
        ]

        response = self.client.compute_routes(
            request=request,
            metadata=metadata,
        )

        routes = response.routes

        if not routes:
            raise ValueError(f"No routes found for {leg}")

        encoded_polyline = routes[0].polyline.encoded_polyline
        distance_km = round(routes[0].distance_meters / 1000.0)

        return Route.from_encoded_polyline(
            encoded_polyline, distance_km, is_accurate=True
        )


def load(trips: Trips, gmaps_api_key: str) -> Routes:
    logger.info("Loading routes")

    route_fetcher = RouteFetcher(gmaps_api_key)
    cache = Cache()

    routes = {}

    for trip in trips:
        for journey in trip.journeys:
            for leg in journey.legs:
                if leg in routes:
                    continue

                if leg.mode_of_transport == ModeOfTransport.PLANE:
                    routes[leg] = LegWrapper(leg).to_fallback_route()
                    continue

                if cached_route := cache.get(leg):
                    routes[leg] = cached_route
                    continue

                logger.info("Fetching route for %s", leg)

                try:
                    route = route_fetcher.fetch(leg)
                except ValueError:
                    logger.warning("Failed to fetch route for %s", leg)
                    route = LegWrapper(leg).to_fallback_route()

                cache[leg] = route
                routes[leg] = route

    return routes
