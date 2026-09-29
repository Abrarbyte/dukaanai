# DukaanAI

AI-assisted business app for small Indian retailers — replaces the paper ledger,
calculator and diary with a mobile app, a REST API and WhatsApp automation.

**Status:** in progress. Runs locally; not deployed.

## Repository layout

| Path | What it is |
| --- | --- |
| `stillnothing/` | Flask REST API (~5.4k lines) |
| `flutter_app/` | Flutter mobile client, `shop_management_app` (~3.9k lines) |

## Backend — `stillnothing/`

Flask 3 + SQLAlchemy, JWT auth with bcrypt, Flask-Limiter with Redis storage.

- **Routes:** auth, onboarding, store, product, sales, bills, customer, payments, reports, ai_insights
- **Models:** user, store, product, sale, bill, customer, udhaar, onboarding
- **Services:** ai_service, whatsapp_service, payment_service (Razorpay), pdf_service (ReportLab), alert_service
- Alembic migrations via Flask-Migrate; health check at `/api/health`
- Deploy config for Railway (`railway.json`, `Procfile`, gunicorn)

### Run locally

```bash
cd stillnothing
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then fill in your own values
flask db upgrade
python run.py
```

Tests: `python test_api.py`, `python test_full_app.py`

## Mobile app — `flutter_app/`

Flutter, organised into `config/ models/ services/ providers/ screens/ widgets/ utils/`.
Screens: splash, login/signup, onboarding, dashboard, products, quick sale.

```bash
cd flutter_app
cp .env.example .env        # point API_URL at your backend
flutter pub get
flutter run
```

## Notes

`.env` files are gitignored — only `.env.example` is tracked. Razorpay and WhatsApp
credentials in the examples are placeholders.
