# Backend

Django API for route generation, checkpoint weather sampling, risk classification, and recommendation.

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

## Vercel

Set the variables in `.env.example`, configure `backend/` as the Vercel project root, and deploy with the included `vercel.json` and `api/index.py` entry point.
