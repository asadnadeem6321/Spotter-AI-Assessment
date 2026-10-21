# Weather-Aware Truck Routing

The project is split into two independently deployable applications:

- `backend/`: Django API for routing, weather sampling, risk rules, and recommendations. Deploy this directory to Vercel as a Python service.
- `frontend/`: React/Vite map interface. Deploy this directory to Vercel.

The backend uses Nominatim for geocoding, OSRM for three route alternatives, and Open-Meteo for hourly weather. The risk and recommendation logic is provider-independent and covered by unit tests.

See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md) for local and deployment setup.

## Project Overview

Weather-Aware Truck Routing helps a driver compare three route options using departure time, load weight, travel time, and weather risk. The interface presents route lines, checkpoint ETAs, risk levels, route summaries, and a 0-48 hour forecast heatmap slider.

## Build Approach

1. Geocode the origin and destination with Nominatim.
2. Request three driving alternatives from OSRM, supplementing provider alternatives with waypoint-constrained routes when needed.
3. Sample each route at the required 10, 25, and 50 mile checkpoint cadence.
4. Query Open-Meteo hourly weather using the truck's estimated arrival time at each checkpoint, including a 49-hour forecast window.
5. Apply the supplied wind, rain, snow, and load-weight rules in provider-independent Python services.
6. Rank routes by severe miles, high miles, average risk, and travel time in that order.
7. Render the results in React with Leaflet map layers and responsive route comparison cards.

## API Routes

- `GET /api/health/` confirms the Django service is available.
- `POST /api/route-plan/` accepts `origin`, `destination`, `departure` (ISO 8601), and `load_weight_lb`, and returns three routes, checkpoints, ETAs, weather, forecast risk, and the recommended route ID.

The backend logic is covered by automated tests for threshold boundaries, load overrides, ETA sampling, route ranking, risk mileage, input validation, and health checks.

## Deployed Connection

The frontend deployment is `https://spotter-ai-assessment-7uy3.vercel.app` and the backend deployment is `https://spotter-ai-assessment-cznj.vercel.app`. The frontend checks `GET /api/health/` and displays the backend connection status. Configure `CORS_ALLOWED_ORIGINS` on the backend with the frontend URL, then redeploy the backend project with `backend/` as its Vercel root.

