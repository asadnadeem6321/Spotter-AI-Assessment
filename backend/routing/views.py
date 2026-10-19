import json
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .providers import build_provider_routes
from .services import RiskLevel, recommend_route


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@require_POST
def route_plan(request):
    try:
        payload = json.loads(request.body)
        origin = payload["origin"].strip()
        destination = payload["destination"].strip()
        departure = datetime.fromisoformat(payload["departure"].replace("Z", "+00:00"))
        load_weight = float(payload["load_weight_lb"])
        if not origin or not destination or load_weight < 0:
            raise ValueError("Origin, destination, and a non-negative load are required")
        routes = build_provider_routes(origin, destination, departure, load_weight)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        return JsonResponse({"error": str(error)}, status=400)
    except OSError as error:
        return JsonResponse({"error": f"External provider unavailable: {error}"}, status=502)

    recommended = recommend_route(routes)
    return JsonResponse(
        {
            "recommended_route_id": recommended.route_id,
            "routes": [_serialize_route(route) for route in routes],
        }
    )


def _serialize_route(route):
    return {
        "id": route.route_id,
        "summary": route.summary,
        "distance_miles": route.distance_miles,
        "duration_minutes": route.duration_minutes,
        "coordinates": route.coordinates,
        "severe_miles": route.severe_miles,
        "high_miles": route.high_miles,
        "average_risk": route.average_risk,
        "checkpoints": [
            {
                "miles": point.miles,
                "latitude": point.latitude,
                "longitude": point.longitude,
                "eta": point.eta.isoformat(),
                "weather": {
                    "wind_mph": point.weather.wind_mph,
                    "rain_in_hr": point.weather.rain_in_hr,
                    "snow_in_hr": point.weather.snow_in_hr,
                },
                "risk": RiskLevel(point.risk).name.lower().replace("_", " "),
                "forecast": [
                    {
                        "wind_mph": weather.wind_mph,
                        "rain_in_hr": weather.rain_in_hr,
                        "snow_in_hr": weather.snow_in_hr,
                        "risk": RiskLevel(risk).name.lower().replace("_", " "),
                    }
                    for weather, risk in point.forecast
                ],
            }
            for point in route.checkpoints
        ],
    }
