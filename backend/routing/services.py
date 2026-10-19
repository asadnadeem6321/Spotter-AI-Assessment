from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import IntEnum
from math import ceil


class RiskLevel(IntEnum):
    LOW = 0
    MODERATE = 1
    HIGH = 2
    SEVERE = 3
    NO_TRAVEL = 4


@dataclass(frozen=True)
class Weather:
    wind_mph: float
    rain_in_hr: float
    snow_in_hr: float


@dataclass(frozen=True)
class Checkpoint:
    miles: float
    latitude: float
    longitude: float
    eta: datetime
    weather: Weather
    risk: RiskLevel
    forecast: list[tuple[Weather, RiskLevel]] = field(default_factory=list)


@dataclass(frozen=True)
class Route:
    route_id: str
    summary: str
    distance_miles: float
    duration_minutes: float
    coordinates: list[tuple[float, float]]
    checkpoints: list[Checkpoint]

    @property
    def severe_miles(self) -> float:
        return self._miles_at_or_above(RiskLevel.SEVERE)

    @property
    def high_miles(self) -> float:
        return self._miles_at_or_above(RiskLevel.HIGH) - self.severe_miles

    def _miles_at_or_above(self, risk_level: RiskLevel) -> float:
        previous_miles = 0.0
        total = 0.0
        for point in self.checkpoints:
            segment_miles = point.miles - previous_miles
            if point.risk >= risk_level:
                total += segment_miles
            previous_miles = point.miles
        return total

    @property
    def average_risk(self) -> float:
        if not self.checkpoints:
            return 0
        return sum(point.risk for point in self.checkpoints) / len(self.checkpoints)

    @property
    def ranking_key(self) -> tuple[float, float, float, float]:
        return (self.severe_miles, self.high_miles, self.average_risk, self.duration_minutes)


def classify_weather(weather: Weather, load_weight_lb: float) -> RiskLevel:
    """Apply the strictest weather condition, then the load-specific overrides."""
    wind_risk = _threshold_risk(weather.wind_mph, (25, 35, 45, 55))
    rain_risk = _threshold_risk(weather.rain_in_hr, (0.10, 0.25, 0.50, 1.00))
    snow_risk = _threshold_risk(weather.snow_in_hr, (0.5, 1.0, 2.0, 3.0))
    base_risk = max(wind_risk, rain_risk, snow_risk)

    if weather.wind_mph >= 55:
        return RiskLevel.NO_TRAVEL
    if 45 <= weather.wind_mph < 55 and load_weight_lb > 30000:
        return RiskLevel.NO_TRAVEL
    if 35 <= weather.wind_mph < 45 and load_weight_lb > 40000:
        return max(base_risk, RiskLevel.SEVERE)
    return base_risk


def _threshold_risk(value: float, thresholds: tuple[float, float, float, float]) -> RiskLevel:
    if value < thresholds[0]:
        return RiskLevel.LOW
    if value < thresholds[1]:
        return RiskLevel.MODERATE
    if value < thresholds[2]:
        return RiskLevel.HIGH
    if value < thresholds[3]:
        return RiskLevel.SEVERE
    return RiskLevel.NO_TRAVEL


def checkpoint_distances(distance_miles: float) -> list[float]:
    """Return weather samples at 10, 25, and 50 mile cadence points."""
    distances = {10.0, 25.0, 50.0}
    distances.update(float(mile) for mile in range(100, ceil(distance_miles) + 1, 50))
    return sorted(distance for distance in distances if distance < distance_miles) + [distance_miles]


def recommend_route(routes: list[Route]) -> Route:
    if not routes:
        raise ValueError("At least one route is required")
    return min(routes, key=lambda route: route.ranking_key)


def build_route(
    route_id: str,
    summary: str,
    distance_miles: float,
    duration_minutes: float,
    coordinates: list[tuple[float, float]],
    departure: datetime,
    load_weight_lb: float,
    weather_for: callable,
    forecast_for: callable | None = None,
) -> Route:
    checkpoints = []
    for miles in checkpoint_distances(distance_miles):
        fraction = miles / distance_miles
        latitude, longitude = coordinates[min(int(fraction * (len(coordinates) - 1)), len(coordinates) - 1)]
        eta = departure + timedelta(minutes=duration_minutes * fraction)
        weather = weather_for(latitude, longitude, eta)
        checkpoint = Checkpoint(
                miles=miles,
                latitude=latitude,
                longitude=longitude,
                eta=eta,
                weather=weather,
                risk=classify_weather(weather, load_weight_lb),
            )
        if forecast_for:
            checkpoint.forecast.extend(
                (forecast, classify_weather(forecast, load_weight_lb))
                for forecast in forecast_for(latitude, longitude, eta)
            )
        checkpoints.append(checkpoint)
    return Route(route_id, summary, distance_miles, duration_minutes, coordinates, checkpoints)
