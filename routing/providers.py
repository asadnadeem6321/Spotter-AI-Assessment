import json
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .services import Weather, build_route


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
    if data.get("code") != "Ok" or len(data.get("routes", [])) < 3:
        raise ValueError("The routing provider returned fewer than 3 route options")
    return data["routes"][:3]


def weather_at(latitude, longitude, eta):
    data = _get_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "wind_speed_10m,rain,snowfall",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "temperature_unit": "fahrenheit",
            "start_date": eta.date().isoformat(),
            "end_date": eta.date().isoformat(),
        },
    )
    times = [datetime.fromisoformat(value).replace(tzinfo=eta.tzinfo) for value in data["hourly"]["time"]]
    index = min(range(len(times)), key=lambda item: abs(times[item] - eta))
    hourly = data["hourly"]
    return Weather(
        wind_mph=hourly["wind_speed_10m"][index],
        rain_in_hr=hourly["rain"][index],
        snow_in_hr=hourly["snowfall"][index],
    )


def build_provider_routes(origin, destination, departure, load_weight):
    routes = []
    for index, route in enumerate(route_options(origin, destination), start=1):
        coordinates = [(latitude, longitude) for longitude, latitude in route["geometry"]["coordinates"]]
        routes.append(
            build_route(
                f"route-{index}",
                f"Option {index}",
                route["distance"] / 1609.344,
                route["duration"] / 60,
                coordinates,
                departure,
                load_weight,
                weather_at,
            )
        )
    return routes
