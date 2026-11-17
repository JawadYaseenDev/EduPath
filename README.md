# EduRecommend — University Guidance App for Pakistan

Helps students find universities and programmes they meet the published requirements for,
based on their education, budget and location. Planning documents are in [`docs/`](docs/);
the required scope is the Workflow PDF (FR-01 to FR-06).

## Project layout

| Folder | What it is |
|---|---|
| `docs/` | Planning documents (requirements, architecture, engine, roadmap...) |
| `backend/` | Python FastAPI backend + eligibility engine + admin API |
| `mobile/` | Student app (Flutter: Android, iOS, web) |
| `admin/` | Staff admin panel (Flutter Web) |

## Status (version 1.0 in progress)

| Area | Status |
|---|---|
| Eligibility engine (rules, 3 groups, explanations, ranking, two no-match paths, strict PDF mode) | Done |
| Backend API for students | Done |
| Admin API: data entry, four-eyes review, change summaries, rule test panel, reports, history, staff | Done |
| Student app | Done; main journeys tested in the browser. Not yet tested on an Android phone |
| Admin panel | Done; tested in the browser incl. review/approve. Two-factor login not built yet |
| Supabase (hosted PostgreSQL + Auth), Alembic migrations, email verification | Not started — local SQLite + local auth for now |
| AI assistant, notifications | Version 1.1 |

Tests: 58 backend (`backend/tests`), 5 student-app widget tests, 1 admin widget test.

### Demo data
The database is seeded with real **reference lists** (provinces, cities, boards, streams,
subjects, entry tests) and **five fictional universities** named "Demo …". They are labelled
**SAMPLE DATA** in the app. No real university data has been entered; that must come from
official sources through the admin panel.

---

## Run everything on your laptop (step by step)

> **Quick way:** `powershell -ExecutionPolicy Bypass -File scripts\setup.ps1` once, then
> `powershell -ExecutionPolicy Bypass -File scripts\start.ps1` every time.
> **Another laptop (nothing installed):** `powershell -ExecutionPolicy Bypass -File scripts\install-everything.ps1` —
> details in [docs/SETUP_ON_ANOTHER_LAPTOP.md](docs/SETUP_ON_ANOTHER_LAPTOP.md).

You need three PowerShell windows: one for the backend, one for the student app, one for the
admin panel. Run each command from the project folder
(`C:\Users\jawad\OneDrive\Desktop\Rahmeen Mobile app project`).

### One-time setup
1. Tools: **uv** (Python) and **Flutter** (installed at `C:\Users\jawad\flutter`) and
   **Google Chrome**. Check them in a *new* PowerShell window:
   ```powershell
   uv --version
   flutter --version
   ```
   If `flutter` is not found, close and reopen PowerShell (it was added to your PATH).
2. Install packages (only the first time, or after pulling new code):
   ```powershell
   cd backend; uv sync --system-certs; cd ..
   cd mobile; flutter pub get; cd ..
   cd admin; flutter pub get; cd ..
   ```
3. Staff login for the admin panel (development only): create `backend\.env` with one line
   `UNIRAH_DEV_STAFF_PASSWORD=<choose a password>`. On start-up the backend then creates
   `admin@example.com` (super admin) and `verifier@example.com` (data verifier) with that
   password. (This PC already has a `backend\.env`.)

### Every time
1. **Window 1 — backend** (keep it open):
   ```powershell
   cd backend; uv run python -m uvicorn app.main:app --port 8000
   ```
   Wait for `Application startup complete`. Check http://localhost:8000/docs.
2. **Window 2 — student app** (opens Chrome):
   ```powershell
   cd mobile; flutter run -d chrome --web-port 5173
   ```
   Create a student account, fill the profile, tap **Find my universities**.
3. **Window 3 — admin panel** (opens Chrome):
   ```powershell
   cd admin; flutter run -d chrome --web-port 5174
   ```
   Sign in as `admin@example.com` with the password from `backend\.env`.
   To approve a change, sign out and sign in as `verifier@example.com`.
4. To stop: press `q` in the Flutter windows and `Ctrl+C` in the backend window.

### Useful extras
- **Reset all data** to the demo start: stop the backend, delete `backend\dev.db`, start again.
- **Run tests**: `cd backend; uv run python -m pytest` · `cd mobile; flutter test` ·
  `cd admin; flutter test`.
- **Hot reload**: while `flutter run` is open, press `r` after changing Dart code.
- **Android emulator**: full step-by-step guide in
  [docs/ANDROID_EMULATOR_SETUP.md](docs/ANDROID_EMULATOR_SETUP.md). In short: install Android Studio (it installs the Android SDK), then
  `cd mobile; flutter run`. The emulator reaches the backend at `10.0.2.2:8000`
  automatically; a real phone needs `--dart-define=API_BASE_URL=http://<your laptop IP>:8000`
  and the backend started with `--host 0.0.0.0`.

### Settings
Environment variables (or `backend/.env`): `UNIRAH_DATABASE_URL`, `UNIRAH_JWT_SECRET`
(required outside development), `UNIRAH_RESULT_MODE` (`extended` or `strict_pdf`),
`UNIRAH_LOAD_DEMO_DATA`, `UNIRAH_DEV_STAFF_PASSWORD`. Real staff accounts:
`cd backend; uv run python -m app.cli create-staff someone@example.com data_editor`.

### Note: Windows Smart App Control
Smart App Control blocks Flutter's shader compiler and SQLAlchemy's compiled speed-ups. It is
turned off on the development PC. The backend uses SQLAlchemy's pure-Python build (see
`backend/pyproject.toml`) so it also works where it is on.
