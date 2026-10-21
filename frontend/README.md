# Frontend

Vite React client for the weather-aware truck routing workflow.

## Local run

```bash
npm install
npm run dev
```

Set `VITE_API_URL` to the deployed backend Vercel URL in the frontend Vercel project. Leave it empty locally so the Vite proxy forwards `/api` to Django.
