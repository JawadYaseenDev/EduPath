# UniRah — University Guidance App for Pakistan

Helps students find universities and programmes they meet the published requirements for,
based on their education, budget and location. Planning documents are in [`docs/`](docs/);
the required scope is the Workflow PDF (FR-01 to FR-06).

## Project layout

| Folder | What it is |
|---|---|
| `docs/` | Planning documents (requirements, architecture, engine, roadmap...) |
| `backend/` | Python FastAPI backend + eligibility engine |
| `mobile/` | Flutter app (Android, iOS, web) |

## Status (version 1.0 in progress)

| Area | Status |
|---|---|
| Eligibility engine (rules, 3 groups, explanations, ranking, two no-match paths, strict PDF mode) | Done, 26 unit tests |
| Backend API: auth, profile, preferences, search, details, recommendations, shortlist, data export/delete | Done, 14 API tests |
| Flutter app: sign-in, 7-step profile setup, dashboard, results, programme details with "why", search & filters, university page, shortlist, compare, profile & privacy | Done; 5 widget tests; main journeys tested in the browser (web build). Not yet tested on an Android phone |
| Admin panel (web) | Not started — next phase |
| Supabase (hosted PostgreSQL + Auth), Alembic migrations, email verification | Not started — local SQLite + local auth for now |
| AI assistant, notifications | Version 1.1 |

### Demo data
The database is seeded with real **reference lists** (provinces, cities, boards, streams,
subjects, entry tests) and **five fictional universities** named "Demo …". They are labelled
**SAMPLE DATA** in the app. No real university data has been entered; that must come from
official sources through the admin panel.

## Run the backend

Needs [uv](https://docs.astral.sh/uv/).

```powershell
cd backend
uv sync
uv run python -m uvicorn app.main:app --port 8000
```

API docs: http://localhost:8000/docs. The SQLite database `backend/dev.db` is created and
seeded on first start (delete it to reset).

Run tests:

```powershell
cd backend
uv run python -m pytest
```

Settings (environment variables, or `backend/.env`): `UNIRAH_DATABASE_URL`,
`UNIRAH_JWT_SECRET` (required outside development), `UNIRAH_RESULT_MODE`
(`extended` or `strict_pdf`), `UNIRAH_LOAD_DEMO_DATA`.

## Run the mobile app

```powershell
cd mobile
flutter pub get
flutter run -d chrome
```

- The app talks to `http://localhost:8000` (web) or `http://10.0.2.2:8000` (Android emulator).
  Override with `--dart-define=API_BASE_URL=https://...`.
- **Android** needs Android Studio (Android SDK + an emulator or a phone).

For automated browser testing, build with `--dart-define=ENABLE_SEMANTICS=true` so the
accessibility tree is available from the start.

### Note: Windows Smart App Control
Smart App Control blocks Flutter's shader compiler and SQLAlchemy's compiled speed-ups. It is
now turned off on the development PC. The backend still uses SQLAlchemy's pure-Python build
(see `backend/pyproject.toml`) so it works on machines where it is on.
