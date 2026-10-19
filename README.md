# Weather-Aware Truck Routing

React and Django application for comparing truck routes using checkpoint weather, load rules, and travel time.

## Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

`POST /api/route-plan/` accepts JSON with `origin`, `destination`, `departure` (ISO 8601), and `load_weight_lb`.

The backend uses Nominatim for geocoding, OSRM for three route alternatives, and Open-Meteo for hourly weather. The risk and recommendation logic is provider-independent and covered by unit tests:

```bash
pytest -q
```
