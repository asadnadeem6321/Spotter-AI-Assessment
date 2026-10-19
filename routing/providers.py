import json
from datetime import datetime, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .services import Weather, build_route, checkpoint_distances


USER_AGENT = "spotter-weather-routing-assessment/1.0"


def _get_json(base_url, params):
    request = Request(
        f"{base_url}?{urlencode(params)}",
        headers={"User-Agent": USER_AGENT},
    )
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def geocode(place):
    results = _get_json(
        "https://nominatim.openstreetmap.org/search",
        {"q": place, "format": "jsonv2", "limit": 1},
    )
    if not results:
        raise ValueError(f"Could not geocode '{place}'")
    return float(results[0]["lat"]), float(results[0]["lon"])


def route_options(origin, destination):
    origin_lat, origin_lon = geocode(origin)
    destination_lat, destination_lon = geocode(destination)
    data = _get_json(
        f"https://router.project-osrm.org/route/v1/driving/{origin_lon},{origin_lat};{destination_lon},{destination_lat}",
        {"alternatives": "true", "overview": "full", "geometries": "geojson"},
    )
    if data.get("code") != "Ok":
        raise ValueError("The routing provider could not calculate a route")

    routes = data.get("routes", [])
    if len(routes) < 3:
        midpoint_lat = (origin_lat + destination_lat) / 2
        midpoint_lon = (origin_lon + destination_lon) / 2
        delta_lat = (destination_lon - origin_lon) * 0.08
        delta_lon = (destination_lat - origin_lat) * 0.08
        for offset in (-1, 1):
            waypoint = f"{midpoint_lon + offset * delta_lon},{midpoint_lat - offset * delta_lat}"
            variant = _get_json(
                f"https://router.project-osrm.org/route/v1/driving/{origin_lon},{origin_lat};{waypoint};{destination_lon},{destination_lat}",
                {"overview": "full", "geometries": "geojson"},
            )
            if variant.get("code") == "Ok":
                routes.extend(variant.get("routes", [])[:1])

    if len(routes) < 3:
        raise ValueError("The routing provider returned fewer than 3 route options")
    return routes[:3]


def _weather_batch(points):
    start = min(eta for _, _, eta in points)
    end = max(eta for _, _, eta in points)
    data = _get_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": ",".join(str(latitude) for latitude, _, _ in points),
            "longitude": ",".join(str(longitude) for _, longitude, _ in points),
            "hourly": "wind_speed_10m,rain,snowfall",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "temperature_unit": "fahrenheit",
            "start_date": start.date().isoformat(),
            "end_date": end.date().isoformat(),
        },
    )
    responses = data if isinstance(data, list) else [data]
    weather_by_point = {}
    for point, response in zip(points, responses):
        times = [datetime.fromisoformat(value).replace(tzinfo=points[0][2].tzinfo) for value in response["hourly"]["time"]]
        eta = point[2]
        index = min(range(len(times)), key=lambda item: abs(times[item] - eta))
        hourly = response["hourly"]
        weather_by_point[point] = Weather(
            wind_mph=hourly["wind_speed_10m"][index],
            rain_in_hr=hourly["rain"][index],
            snow_in_hr=hourly["snowfall"][index],
        )
    return weather_by_point


def build_provider_routes(origin, destination, departure, load_weight):
    routes = []
    for index, route in enumerate(route_options(origin, destination), start=1):
        coordinates = [(latitude, longitude) for longitude, latitude in route["geometry"]["coordinates"]]
        distance_miles = route["distance"] / 1609.344
        duration_minutes = route["duration"] / 60
        points = []
        for miles in checkpoint_distances(distance_miles):
            fraction = miles / distance_miles
            latitude, longitude = coordinates[min(int(fraction * (len(coordinates) - 1)), len(coordinates) - 1)]
            points.append((latitude, longitude, departure + timedelta(minutes=duration_minutes * fraction)))
        weather_by_point = _weather_batch(points)

        def weather_for(latitude, longitude, eta):
            return weather_by_point[(latitude, longitude, eta)]

        routes.append(
            build_route(
                f"route-{index}",
                f"Option {index}",
                distance_miles,
                duration_minutes,
                coordinates,
                departure,
                load_weight,
                weather_for,
            )
        )
    return routes
