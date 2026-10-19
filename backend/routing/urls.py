from django.urls import path

from .views import health, route_plan

urlpatterns = [
    path("health/", health, name="health"),
    path("route-plan/", route_plan, name="route-plan"),
]
