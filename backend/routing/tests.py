from datetime import datetime, timezone

import pytest
from django.test import Client

from routing.services import RiskLevel, Route, Weather, build_route, classify_weather, recommend_route


@pytest.mark.parametrize(
    ("weather", "expected"),
    [
        (Weather(24.9, 0, 0), RiskLevel.LOW),
        (Weather(25, 0, 0), RiskLevel.MODERATE),
        (Weather(35, 0, 0), RiskLevel.HIGH),
        (Weather(45, 0, 0), RiskLevel.SEVERE),
        (Weather(55, 0, 0), RiskLevel.NO_TRAVEL),
        (Weather(0, 1.01, 0), RiskLevel.NO_TRAVEL),
        (Weather(0, 0, 3.01), RiskLevel.NO_TRAVEL),
    ],
)
def test_weather_thresholds(weather, expected):
    assert classify_weather(weather, 20000) == expected


def test_load_overrides_wind_risk():
    assert classify_weather(Weather(50, 0, 0), 30000) == RiskLevel.SEVERE
    assert classify_weather(Weather(50, 0, 0), 30001) == RiskLevel.NO_TRAVEL
    assert classify_weather(Weather(40, 0, 0), 40001) == RiskLevel.SEVERE


def test_recommendation_uses_required_priority_order():
    routes = [
        Route("slow", "", 100, 300, [], []),
        Route("fast", "", 100, 100, [], []),
    ]
    assert recommend_route(routes).route_id == "fast"


def test_build_route_uses_eta_for_weather_sampling():
    seen = []

    def weather_for(latitude, longitude, eta):
        seen.append(eta)
        return Weather(20, 0, 0)

    route = build_route(
        "route-1", "test", 60, 120, [(1, 2), (3, 4)], datetime(2026, 1, 1, tzinfo=timezone.utc), 20000, weather_for
    )
    assert route.checkpoints[-1].eta == datetime(2026, 1, 1, 2, tzinfo=timezone.utc)
    assert seen == [point.eta for point in route.checkpoints]


def test_health_endpoint():
    response = Client().get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_route_plan_rejects_invalid_load():
    response = Client().post(
        "/api/route-plan/",
        data={
            "origin": "New York, NY",
            "destination": "Washington, DC",
            "departure": "2026-10-19T08:00:00+00:00",
            "load_weight_lb": -1,
        },
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "non-negative" in response.json()["error"]
