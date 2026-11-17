# System Architecture

This document explains **which technologies we recommend, why, and how the parts connect.**

---

## 1. What the system must handle (drivers for our choices)

Before choosing tools, here is what makes this project special:

1. **The data is relational.** University → campus → programme → offering per year → rules, fees, tests, hostels. We need joins, filters, and strong consistency. This points to a **relational (SQL) database**.
2. **Eligibility rules are complex but must be exact.** We need a proper backend language with good testing, not logic spread across mobile code.
3. **RAG chatbot.** Needs text processing, PDF reading (prospectuses), embeddings, and vector search. The **Python** ecosystem is the strongest here.
4. **Small team, limited budget.** We want managed services (no server babysitting) and low fixed cost.
5. **Data changes every admission season.** We need an admin panel, change history, and verification workflow.
6. **Students are on mid-range Android phones with variable internet.**

---

## 2. Technology comparison

### 2.1 Backend platform and database

| Option | Good | Bad | Fit |
|---|---|---|---|
| **Firebase** (Firestore + Auth + Functions) | Very fast to start; great Flutter support; generous free tier; push notifications built in | Firestore is a document (NoSQL) database: no joins, weak multi-filter queries (e.g., "province IN [...] AND fee < X AND hostel = true AND programme field IN [...]"), data is duplicated, harder to keep consistent. Vector search exists but is limited. Costs grow with every document read, which is hard to predict for search-heavy apps. | ⚠️ Weak for our core data |
| **Supabase** (managed PostgreSQL + Auth + Storage + Row-Level Security + pgvector) | Real SQL database with joins, constraints, and transactions; built-in auth with JWT; row-level security; **pgvector** gives vector search in the same database (no extra vector DB); file storage for prospectus PDFs; good Flutter SDK; open source (can self-host later to avoid lock-in); predictable pricing | Smaller ecosystem than Firebase; server logic in Edge Functions is TypeScript/Deno (we would still add our own Python service) | ✅ **Strong fit** |
| **Self-managed PostgreSQL + custom auth** (e.g., on a VPS) | Full control, cheapest at large scale | We must build auth, backups, security patches, scaling ourselves. Too much work for a small team. | ❌ Not for MVP |
| **AWS/GCP full stack** (RDS/Cloud SQL, Cognito/Identity Platform, etc.) | Very scalable, enterprise-grade | More complex setup, more cost, more DevOps skills needed | ⚠️ Overkill for MVP; possible later |

### 2.2 Backend API language / framework

| Option | Good | Bad | Fit |
|---|---|---|---|
| **FastAPI (Python)** | Fast to write; automatic API docs (OpenAPI); strong typing with Pydantic; best libraries for RAG, PDF parsing, text processing; easy unit testing of the rule engine | Python is slower than Go/Node for heavy traffic (not a problem at our scale) | ✅ **Recommended** |
| **Node.js (NestJS / Express)** | Large ecosystem; same language as a React admin panel | Weaker AI/PDF/data tooling than Python | ⚠️ OK |
| **Supabase Edge Functions only** | No separate server | Short time limits; harder to build a large, well-tested rule engine and RAG pipeline | ⚠️ Use only for small tasks |
| **Dart backend (Dart Frog / Serverpod)** | Same language as Flutter | Small ecosystem, few AI libraries | ❌ |

### 2.3 Vector database (for the chatbot)

| Option | Good | Bad | Fit |
|---|---|---|---|
| **pgvector inside Supabase Postgres** | No extra service or bill; can join vectors with normal tables (e.g., filter by university, year, verification status); backups included | Slower than dedicated vector DBs at tens of millions of vectors (we will have tens of thousands) | ✅ **Recommended** |
| Pinecone / Qdrant / Weaviate | Very fast at huge scale, nice features | Extra cost, extra service, data must be synced from Postgres | ❌ Not needed now |

### 2.4 Admin panel

| Option | Good | Bad | Fit |
|---|---|---|---|
| **Separate web app in React (Next.js) + an admin framework (e.g., Refine) + a component library** | Excellent data tables, forms, file upload; many ready admin features; web-native | Second language (TypeScript) for the team | ✅ **Recommended** if someone knows React |
| **Separate web app in Flutter Web** | Same language (Dart); can share data models with the mobile app | Weaker for large data tables and complex forms; bigger first load; less mature for admin tools | ✅ Good alternative if the team knows only Flutter |
| Admin screens inside the mobile app | One codebase | Data entry on a phone is slow and error-prone; mixes admin security risks into the student app | ❌ |
| Use Supabase Studio directly | Zero work | No verification workflow, no rule builder, too risky for non-technical editors | ❌ (developers only) |

**Decision needed** from the owner: React or Flutter Web for admin. See [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

### 2.5 AI model provider

Details in [RAG_CHATBOT_ARCHITECTURE.md](RAG_CHATBOT_ARCHITECTURE.md). Summary:

- **Language model:** Anthropic Claude through the official API. Default: `claude-opus-5-5` (best quality). Cheaper options to test against our quality checks: `claude-sonnet-5-5`, `claude-haiku-5-5`. The final choice is the owner's decision, based on measured quality and budget.
- **Embeddings:** Anthropic does not offer an embedding model. Recommended: a multilingual embedding model that handles English, Urdu, and Roman Urdu (for example Voyage AI multilingual models, or an open-source model such as BGE-M3 / multilingual-E5 hosted ourselves). We will test 2–3 on our own question set before choosing.
- We keep the AI provider behind one small interface in the backend, so it can be changed later.

### 2.6 Final recommended stack

| Layer | Choice |
|---|---|
| Mobile app | **Flutter** (stable channel), Dart 3 |
| State management | **Riverpod** (testable, no `BuildContext` needed, good for async data) |
| Navigation | **go_router** (deep links, auth redirects) |
| HTTP client | **dio** (interceptors for tokens, retries) |
| Data models | **freezed** + **json_serializable** |
| Local cache / offline | **drift** (SQLite) for catalogue cache and saved items; **flutter_secure_storage** for tokens |
| Forms | **flutter_form_builder** or **reactive_forms** |
| Translations | Flutter `gen-l10n` (ARB files) — English now, Urdu later (right-to-left ready) |
| Auth | **Supabase Auth** (email/password, Google, phone OTP) |
| Database | **Supabase PostgreSQL** (+ **pgvector**, + `pg_trgm` for fuzzy search) |
| File storage | **Supabase Storage** (prospectus PDFs, screenshots, logos) |
| Backend API | **FastAPI (Python 3.12+)**, SQLAlchemy 2 + Alembic migrations, Pydantic |
| Background jobs | Simple job queue (e.g., a Postgres-based queue or a scheduled job on the host) for re-indexing, link checks, reminders |
| AI | Anthropic Claude API + a multilingual embedding model |
| Push notifications | **Firebase Cloud Messaging** (only for push; not as our database) |
| Crash reporting | Sentry or Firebase Crashlytics |
| Admin panel | Next.js + Refine (or Flutter Web) |
| Hosting (API) | A container platform that scales automatically, e.g., Google Cloud Run, Render, Fly.io, or Railway |
| Region | Closest available to Pakistan (e.g., Mumbai or Singapore) — confirm latency and data-location rules |
| CI/CD | GitHub Actions |

---

## 3. High-level architecture

```
┌───────────────────────┐        ┌──────────────────────┐
│  Flutter Student App  │        │  Admin Web Panel     │
│  (Android / iOS)      │        │  (React or Flutter)  │
└──────────┬────────────┘        └──────────┬───────────┘
           │ HTTPS + JWT                    │ HTTPS + JWT + 2FA
           │                                │
           │  (sign-in only)                │
           ├──────────────►┌────────────────┴───────┐
           │               │   Supabase Auth        │
           │               └────────────────────────┘
           ▼
┌──────────────────────────────────────────────────────────┐
│                FastAPI Backend (/v1)                     │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌───────────┐  │
│  │ Profile  │ │Catalogue │ │Eligibility │ │ Chat /    │  │
│  │ module   │ │ & search │ │  engine    │ │ RAG       │  │
│  └──────────┘ └──────────┘ └────────────┘ └─────┬─────┘  │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐       │        │
│  │ Admin &  │ │ Notifi-  │ │ Background │       │        │
│  │ verify   │ │ cations  │ │   jobs     │       │        │
│  └──────────┘ └──────────┘ └────────────┘       │        │
└───────┬───────────────────────────┬─────────────┼────────┘
        │ SQL                       │             │ HTTPS
        ▼                           ▼             ▼
┌───────────────────────┐  ┌──────────────┐  ┌───────────────────┐
│ Supabase PostgreSQL   │  │ Supabase     │  │ Claude API        │
│ - core data           │  │ Storage      │  │ Embedding API     │
│ - pgvector (chunks)   │  │ (PDFs, logos)│  └───────────────────┘
│ - row-level security  │  └──────────────┘
└───────────────────────┘
                                   ┌───────────────────┐
                                   │ Firebase Cloud    │
                                   │ Messaging (push)  │
                                   └───────────────────┘
```

### Why the app talks to FastAPI (not directly to the database)
- All business rules live in **one place** (the backend), so the app stays simple and old app versions keep working.
- We can change data structures without forcing app updates.
- Secrets and AI keys stay on the server.
- The app only uses the Supabase SDK for **sign-in**. It sends the Supabase token to FastAPI, which checks it on every request.

---

## 4. Backend modules

| Module | Responsibility |
|---|---|
| **auth** | Check JWT, load user + role, enforce permissions |
| **profile** | Student personal info, qualifications, subjects, test scores, preferences, consent |
| **reference** | Provinces, cities, boards, qualification types, groups, subjects, programme fields (lookup lists) |
| **catalogue** | Universities, campuses, programmes, offerings, fees, hostels, entry tests, deadlines; search |
| **eligibility** | Rule evaluation, category assignment, explanations, ranking, saving results |
| **chat** | RAG pipeline, conversation history, feedback, limits |
| **knowledge** | Ingest and index documents and FAQs into vectors |
| **admin** | CRUD with verification workflow, audit log, review queues |
| **notifications** | Deadline reminders, data-change alerts |
| **jobs** | Scheduled tasks: link checking, stale-data detection, re-indexing |

Each module has its own folder, routes, services, and tests. Modules talk through service functions, not by reading each other's tables directly. This keeps the code easy to split later if needed.

---

## 5. Key data flows

### 5.1 Get recommendations
1. App calls `POST /v1/recommendations/run`.
2. Backend loads the student's profile + preferences.
3. Engine loads all **published** offerings for the current admission year (cached in memory, refreshed when admins publish).
4. Engine evaluates rules → category + reasons for each offering.
5. Engine applies preference filters and ranking.
6. Result is saved (`recommendation_runs` + `recommendation_results`) with the data version.
7. App shows grouped results.

### 5.2 Ask the chatbot
1. App sends question to `POST /v1/chat/messages` (streaming response).
2. Backend classifies the question (app help / admissions / my results / off-topic).
3. Backend retrieves relevant chunks from pgvector + structured facts from SQL.
4. Backend builds a prompt with the retrieved sources and calls the LLM.
5. Answer streams back with source links. Logged for review.

### 5.3 Admin updates a fee
1. Editor changes a fee and attaches the source (URL or PDF page).
2. Record status → **Pending verification**.
3. A Verifier reviews and approves → **Verified / Published**.
4. Change history saved. Catalogue cache refreshed. Related chatbot chunks re-indexed. Students who saved that programme are notified (optional).

---

## 6. Security design

| Area | Approach |
|---|---|
| Authentication | Supabase Auth; email verification; optional Google and phone OTP; refresh-token rotation |
| Passwords | Hashed by Supabase Auth (bcrypt). Minimum length 8, checked against common-password list |
| Authorization | Roles: `student`, `support`, `data_editor`, `data_verifier`, `super_admin`. Checked in FastAPI on each endpoint |
| Database | Row-level security (RLS) policies as a second safety layer: students can only access rows where `user_id = auth.uid()`. The backend uses a limited database role, not the master key |
| API | HTTPS only; input validation (Pydantic); rate limits per user and per IP; CORS restricted to admin domain; request size limits |
| Secrets | Stored in the host's secret manager; never in the app or in git |
| Admin | 2FA required; IP allow-list optional; every write action in `audit_log` |
| Personal data | Minimise; sensitive optional fields encrypted at column level if stored; backups encrypted |
| Chatbot | No write tools; only the logged-in student's own data is passed; system instructions ignore instructions found inside documents; output never shown as "verified" unless it came from verified fields |
| Mobile | Tokens in secure storage; certificate pinning considered after MVP; code obfuscation for release builds |
| Monitoring | Alerts on login failure spikes and unusual admin activity |

---

## 7. Environments and deployment

| Environment | Purpose |
|---|---|
| Development | Each developer; local Supabase (Docker) + local FastAPI |
| Staging | Copy of production setup with test data; used for QA and admin training |
| Production | Real students |

- Database changes through **Alembic migrations** only (reviewed in pull requests).
- Mobile releases through Google Play internal → closed testing → production tracks.
- FastAPI deployed as a Docker container through GitHub Actions.

---

## 8. Estimated monthly cost (MVP, rough)

These are rough planning numbers and must be checked against current price pages.

| Item | Rough monthly cost |
|---|---|
| Supabase (Pro plan) | ~USD 25 |
| API hosting (auto-scaling container) | ~USD 0–30 |
| AI model + embeddings (depends on model and usage; with limits and caching) | ~USD 20–100+ |
| Push notifications (FCM) | Free |
| Domain, email sending | ~USD 5–10 |
| Google Play developer account | USD 25 one time |
| Apple developer account (if iOS) | USD 99 per year |

The AI cost depends heavily on which Claude model is chosen and on message volume — see the chatbot document for how to measure it.
