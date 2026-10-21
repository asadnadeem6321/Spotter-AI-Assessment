# Frontend

Vite React client for the weather-aware truck routing workflow.

## Local run

```bash
npm install
npm run dev
```

Set `VITE_API_URL` to the deployed backend Vercel URL in the frontend Vercel project. Leave it empty locally so the Vite proxy forwards `/api` to Django.

After deployment, the header shows `Backend connected` when the frontend receives `GET /api/health/` from the backend. If it shows `Backend unavailable`, check that `VITE_API_URL` is the backend Vercel URL and that the backend `CORS_ALLOWED_ORIGINS` contains the frontend Vercel URL. Redeploy the frontend after changing `VITE_API_URL`, because Vite embeds it during the build.
