# LeadHawk

A FastAPI backend with two parts:

- **Account API** — registration, email verification, and JWT-authenticated access to the current user's profile.
- **Agent 1 (business discovery)** — finds local businesses with a weak online presence (low rating, few reviews, no or broken website) for a given city + category, and stores them as leads. Agent 2 (outreach) is out of scope.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Create a PostgreSQL database, set `DATABASE_URL` and a long random `JWT_SECRET_KEY` in `.env`. For Agent 1, also set `GOOGLE_PLACES_API_KEY` (a Google Cloud key with "Places API (New)" enabled). `LEAD_MIN_RATING` and `LEAD_MIN_REVIEWS` control the weak-presence filter thresholds and default to `3.5` and `10`. Then run:

```powershell
uvicorn app.main:app --reload
```

The application creates tables for a new development database at startup. Use migrations (for example Alembic) before changing an existing or production database schema.

## Endpoints

**Account**
- `POST /api/v1/user/create` — creates an inactive account and sends a verification email when SMTP is configured.
- `POST /api/v1/user/verify` — activates an account using the eight-character verification code; codes expire after 15 minutes.
- `POST /api/v1/user/login` — returns a bearer JWT for an active account.
- `GET`, `PATCH`, `DELETE /api/v1/user/me` — require `Authorization: Bearer <access_token>` and operate only on the caller.

**Leads (Agent 1)**
- `POST /api/v1/leads/generate` — body `{"city": "...", "category": "..."}`. Runs the discovery pipeline for that search and returns the newly stored leads.
- `GET /api/v1/leads` — lists stored leads, optionally filtered by `city` and `category`, with a `limit` (default 50, max 200).

**Other**
- `GET /api/v1/health` — basic service health response.

SMTP delivery is intentionally optional for local development. Do not expose the API publicly without rate limiting, a real email delivery/retry workflow, and database migrations.

## Agent 1 pipeline

For a given `city` + `category`:

1. **Crawl** — search Google Places (`searchText`) for matching listings.
2. **Parse** — extract name, rating, review count, phone, website, address; records missing an id/name are dropped rather than stored as garbage.
3. **Filter** — keep only listings with a weak online presence: no or unreachable website (checked live), rating below `LEAD_MIN_RATING`, or review count below `LEAD_MIN_REVIEWS`. Any one of these qualifies a listing; strong-presence businesses are discarded, not stored.
4. **Clean + dedupe** — normalize business name and address (case, punctuation, legal suffixes like "LLC") and skip anything already stored, matched by source place id or by the normalized name/address. Catches the same business resurfacing under a different search or source.
5. **Store** — write the resulting lead records.

Owner name / contact email enrichment (the fifth step in the original design) is not implemented yet — `owner_name`, `owner_email`, and `contact_source` columns exist on the `Lead` model but stay `null`. Only one source (Google Places) is wired up; Yelp or other sources would slot into the same crawl step.
