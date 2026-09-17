# LeadHawk account API

A small FastAPI boilerplate for account registration, email verification, and JWT-authenticated access to the current user's profile.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Create a PostgreSQL database, set `DATABASE_URL` and a long random `JWT_SECRET_KEY` in `.env`, then run:

```powershell
uvicorn app.main:app --reload
```

The application creates tables for a new development database at startup. Use migrations (for example Alembic) before changing an existing or production database schema.

## Endpoints

- `POST /api/v1/user/create` — creates an inactive account and sends a verification email when SMTP is configured.
- `POST /api/v1/user/verify` — activates an account using the eight-character verification code; codes expire after 15 minutes.
- `POST /api/v1/user/login` — returns a bearer JWT for an active account.
- `GET`, `PATCH`, `DELETE /api/v1/user/me` — require `Authorization: Bearer <access_token>` and operate only on the caller.
- `GET /api/v1/health` — basic service health response.

SMTP delivery is intentionally optional for local development. Do not expose the API publicly without rate limiting, a real email delivery/retry workflow, and database migrations.
