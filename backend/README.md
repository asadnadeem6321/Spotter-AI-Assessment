# Backend

Django API for route generation, checkpoint weather sampling, risk classification, and recommendation.

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

## Railway

Set the variables in `.env.example`, deploy this directory as the Railway root, and Railway will use the included `Procfile`.
