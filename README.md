# Weather-Aware Truck Routing

The project is split into two independently deployable applications:

- `backend/`: Django API for routing, weather sampling, risk rules, and recommendations. Deploy this directory to Railway.
- `frontend/`: React/Vite map interface. Deploy this directory to Vercel.

The backend uses Nominatim for geocoding, OSRM for three route alternatives, and Open-Meteo for hourly weather. The risk and recommendation logic is provider-independent and covered by unit tests.

See [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md) for local and deployment setup.
