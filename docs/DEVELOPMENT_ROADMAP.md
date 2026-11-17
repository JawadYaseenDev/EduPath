# Development Roadmap

## 1. Changes to the suggested phases (and why)

The original brief listed phases one after another. We recommend these changes:

1. **Data collection starts in week 1 and runs in parallel.** Data is the biggest risk. Without verified data, the engine and chatbot have nothing to work with. A data team starts with spreadsheets while developers build the admin panel.
2. **The recommendation engine moves earlier** (before most of the Flutter UI). It is the core value and the hardest logic. Building it early with tests shows quickly whether our data model works.
3. **A basic admin panel comes before the full mobile app**, so data can be entered into the real database early.
4. **The chatbot comes after the engine and data** because it depends on both.
5. **Testing is continuous**, not only at the end.
6. **A pilot scope** for the first release (not all of Pakistan at once).

## 1a. Baseline vs extensions

The Workflow PDF (FR-01 to FR-06) is the **baseline**. Phases are labelled so the baseline can be delivered first if needed:

| Part | Baseline (PDF) | Extension |
|---|---|---|
| Auth, profile, preferences | FR-01, FR-02 | Phone OTP, guest mode, Urdu |
| Admin data management | FR-03 | Rule-change impact preview, AI-assisted PDF extraction |
| Engine, explanations, no-match handling | FR-04 | Potentially Eligible group is part of the core design (needed for correct results) |
| Search, filters, compare | FR-05 | Map view |
| Shortlist, official links | FR-06 | Deadline reminders, data-change alerts |
| AI assistant (Phase 6) | — | Whole phase is an extension |

**Decision (confirmed by the owner): the PDF is a fixed required specification.** Therefore:
- **Version 1.0** = the baseline (FR-01 to FR-06): Phases 0–5, the polish part of Phase 7, and Phase 8. About **4½–5 months**.
- **Version 1.1** = extensions: Phase 6 (AI assistant) and notifications from Phase 7. About **5–6 more weeks**.
- Changes to the PDF's workflow diagram (Potentially Eligible group, two no-match paths) need supervisor approval. See [CHANGE_REQUEST_FOR_SUPERVISOR.md](CHANGE_REQUEST_FOR_SUPERVISOR.md). Until approved, the engine is built so it can run in **strict PDF mode** (see [RECOMMENDATION_ENGINE.md § 0.1](RECOMMENDATION_ENGINE.md#01-strict-pdf-mode-fallback)).

## 2. Proposed MVP pilot scope (needs owner approval)

| Item | Proposal |
|---|---|
| Regions | All regions supported in the system; **data** first for Punjab + Islamabad + one more (e.g., Sindh or KP), then expand |
| Universities | ~40–60 (mix of public, private, semi-government; include women's universities) |
| Programme families | Computing (CS, SE, AI, IT, DS), Engineering (EE, ME, CE, + Engineering Technology for DAE), Business (BBA, BS Accounting & Finance), Medical/Allied (MBBS/BDS via MDCAT rules, Pharm-D, DPT) |
| Qualifications | Matric (Science/Arts), O-Levels, FSc Pre-Eng, FSc Pre-Med, ICS, I.Com, FA, A-Levels, DAE |
| Platform | Android first; iOS after MVP |
| Language | English; Urdu after MVP |

## 3. Phases

Time estimates assume a small team: **2 developers (1 Flutter, 1 backend/AI), 1 part-time designer, 2 part-time data entry/verifiers, 1 project lead/QA**. Adjust once the real team size is known.

### Phase 0 — Approval and setup (Week 1–2)
- Review and approve these documents; answer open questions.
- Create accounts: GitHub, Supabase, hosting, AI provider, Google Play developer, domain.
- Repository structure, coding standards, CI pipeline, environments (dev/staging/prod).
- Data team: build the pilot university list; collect official prospectuses; set up a shared spreadsheet template matching the database design.

**Done when:** documents approved, repos and environments ready, pilot list agreed.

### Phase 1 — Detailed design (Week 2–4)
- Wireframes for all mobile screens; test the profile wizard with 5–8 students.
- Final database schema and migrations plan.
- Rule types finalised with real examples from 10 prospectuses (to make sure the rule format covers real cases).
- API contract (OpenAPI) for main endpoints.
- Golden test set v1: 50 student profiles with expected results, reviewed by a counsellor.

**Done when:** wireframes approved, schema reviewed, 10 real prospectuses fit the rule format.

### Phase 2 — Database + backend foundation (Week 4–7)
- Supabase project, migrations, reference data seed (regions, boards, groups, subjects...).
- FastAPI skeleton: auth middleware, roles, error handling, logging, rate limiting.
- Profile APIs (qualifications, subjects, tests, preferences, consents).
- Catalogue APIs (universities, campuses, programmes, offerings, search with filters).
- Row-level security policies + tests.

**Done when:** profile and catalogue APIs work with tests on staging.

### Phase 3 — Admin panel v1 (Week 6–10)
- Login + 2FA, roles.
- Reference data, universities, campuses, programmes, offerings, fees, hostels, tests, deadlines.
- Rule builder + test panel.
- Sources upload, verification workflow, publish, audit log.
- Data team moves from spreadsheets into the admin panel.

**Done when:** data team can enter and verify a full university without developer help.

### Phase 4 — Recommendation engine (Week 7–11)
- Input normalisation, rule evaluators for all initial rule types, rule sets, categories.
- Preference checks, match score, explanation templates, next steps, alternatives.
- Save runs with versions.
- Golden test set grows to 200+ profiles; automated test run in CI.

**Done when:** 100% of golden tests pass; run time < 2 s; explanations reviewed by a counsellor.

### Phase 5 — Flutter app (Week 8–16)
- App architecture: Riverpod, go_router, dio, drift cache, theme, translations setup.
- Auth screens, onboarding, profile wizard, preferences.
- Results summary, lists, detail/"why" screen, alternatives.
- Explore (search, filters, university and programme pages).
- Shortlist, compare, deadlines, settings, privacy (export/delete).
- Report incorrect info.
- Crash reporting, analytics (no personal data).

**Done when:** all MVP journeys work end-to-end on staging on real low/mid-range phones.

### Phase 6 — AI assistant → **moved to version 1.1** (about 5–6 weeks after v1.0)
*Not in the baseline PDF. The data model and backend keep the chat module's place so it can be added without redesign.*
- KB tables, embedding model chosen by testing, ingestion jobs.
- App-help + guides content written (~40 articles).
- RAG pipeline: router, hybrid search, generation with citations, number check, guardrails.
- My-results explanations; admissions cards auto-generated from verified data.
- Chat UI with streaming, sources, feedback.
- Evaluation set (~300 questions) and model comparison (quality vs cost) → owner picks the model.

**Done when:** evaluation targets met (near-zero invented facts, ≥95% citations on admissions answers).

### Phase 7 — Polish (Week 16–17); notifications in version 1.1
- *(v1.1)* Deadline reminders, data-change alerts (FCM).
- Performance tuning, offline behaviour, accessibility pass, empty/error states.
- Content: privacy policy, terms, "where our data comes from" page (legal review).

### Phase 8 — Testing and launch (Week 17–21)
- Full test pass: unit, widget, integration, API, recommendation accuracy (chatbot evaluation in v1.1).
- Acceptance check against every bullet of PDF FR-01 to FR-06 (traceability table in FUNCTIONAL_REQUIREMENTS.md § 0.1).
- Security testing (OWASP Mobile + API checklists), RLS tests, dependency scan.
- Load test for admission-season traffic.
- Closed beta with 50–200 students (schools/colleges/academies); fix issues.
- Google Play release (internal → closed → production).
- Monitoring and on-call plan for admission season.

**Done when:** beta feedback addressed, no critical bugs, data for pilot scope verified for the current cycle.

### Version 1.0 total: about **4½–5 months** with the team above. Version 1.1 (AI assistant + notifications): about **5–6 more weeks**.

```
Week:        1   3   5   7   9   11  13  15  17  19  21  23  25  27
Phase 0     ██
Phase 1      ████
Phase 2         ██████
Phase 3             ████████
Phase 4               ████████
Phase 5                   ████████████████
Phase 7 (polish)                          ███
Phase 8                                     ████████
── v1.0 release ──────────────────────────────────────┤
Phase 6 (v1.1)                                        ██████████
Notifications (v1.1)                                      ████
Data entry  ██████████████████████████████████████████████████████ (continuous)
```

## 4. After MVP (Version 1.x / 2)

| Order | Feature |
|---|---|
| 1 | Expand data to all regions and more programme families |
| 2 | iOS release |
| 3 | Urdu language (UI + chatbot) |
| 4 | Merit/aggregate calculator + past closing merit (history only) |
| 5 | Scholarships and financial aid database |
| 6 | AI-assisted prospectus extraction for admins (human-verified) |
| 7 | University partner portal (universities suggest corrections) |
| 8 | Counsellor/teacher accounts for schools |
| 9 | Postgraduate programmes |

## 5. Team roles needed

| Role | Work |
|---|---|
| Project lead / product owner | Priorities, approvals, contact with universities and schools |
| Flutter developer | Mobile app |
| Backend + AI developer | FastAPI, database, engine, RAG |
| Admin panel developer | Can be the backend dev (React) or Flutter dev (Flutter Web) |
| UI/UX designer (part-time) | Wireframes, design system, user testing |
| Data editors + verifier (part-time, at least 2 people) | Collect, enter, verify data |
| Education counsellor / advisor (part-time) | Review rules, golden tests, explanations, guides |
| QA (can be shared) | Test plans, regression |

## 6. Ways of working

- Two-week sprints with a demo at the end of each.
- Every change through a pull request with review and passing tests.
- Update these documents when decisions change.
- Track tasks in a board (e.g., GitHub Projects, Jira, or Trello).
