# Cert Tracker

A small FastAPI service for tracking study progress across the certs I'm
juggling right now (AZ-900, DP-900, GitHub Copilot Fundamentals, ...) and
answering the one question that matters most evenings: **what should I
study next?**

## Getting started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Then open **http://127.0.0.1:8000/docs** for interactive Swagger docs.

Run the tests with:

```bash
pytest -v
```

Data is stored in a local `cert_tracker.db` SQLite file, created automatically.

## Readiness score