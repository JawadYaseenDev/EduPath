# Non-Functional Requirements

These describe **how well** the system must work, not **what** it does.

---

## 1. Performance

| ID | Requirement |
|---|---|
| PERF-01 | App cold start under 3 seconds on a mid-range Android phone (e.g., 4 GB RAM, 2021 or newer). |
| PERF-02 | University list and search results load in under 1.5 seconds on a 4G connection. |
| PERF-03 | A full recommendation run (all programmes in the database for one student) finishes in under 2 seconds on the server. |
| PERF-04 | Chatbot: first words appear within 3 seconds (streaming); full answer usually within 10 seconds. |
| PERF-05 | App size under 30 MB download. |
| PERF-06 | Works on slow 3G / patchy connections: show cached data, retry automatically, never lose a half-filled form. |

## 2. Scalability

| ID | Requirement |
|---|---|
| SCAL-01 | MVP target: 10,000 registered students, 500 at the same time during admission season. |
| SCAL-02 | Design should grow to 200,000+ students and all ~250+ HEC-recognised universities and their campuses without redesign. |
| SCAL-03 | Admission season (June–September) traffic can be 10× normal. Server must scale up without code changes. |
| SCAL-04 | Adding a new province/region, university, programme, qualification type, board, or rule type must be possible by data entry (no app release). New **kinds** of rule may need a backend update, but not a mobile app update. |

## 3. Reliability and Availability

| ID | Requirement |
|---|---|
| REL-01 | 99.5% uptime for the API (about 3.6 hours downtime per month max). |
| REL-02 | Daily automatic database backups, kept for 30 days. Test a restore once per quarter. |
| REL-03 | If the AI service is down, the rest of the app works normally; the chat shows a friendly message. |
| REL-04 | Recommendation results are saved with the data version used, so we can explain any past result. |

## 4. Accuracy and Data Quality

| ID | Requirement |
|---|---|
| DATA-01 | No eligibility rule, fee, or deadline is shown to students unless it has an official source and is marked **Verified**. |
| DATA-02 | Every shown record displays its "last verified" date and admission year. |
| DATA-03 | Data from a previous admission year is shown with a warning, never silently. |
| DATA-04 | The eligibility engine is **deterministic**: same input + same data version = same output, every time. |
| DATA-05 | A regression test set of at least 200 student profiles with expected results is run before every rule or engine release. |
| DATA-06 | AI-generated text is always visually marked as AI and kept separate from verified data fields. |

## 5. Security

Detailed design is in [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md#security-design).

| ID | Requirement |
|---|---|
| SEC-01 | All traffic over HTTPS (TLS 1.2+). |
| SEC-02 | Passwords never stored by us in plain form; handled by the auth provider with strong hashing (bcrypt/argon2). |
| SEC-03 | Short-lived access tokens (≤1 hour) with refresh tokens; refresh tokens can be revoked. |
| SEC-04 | Database row-level security: a student can only read and change their own profile data. |
| SEC-05 | Role-based access for admins; least privilege; all admin actions logged. |
| SEC-06 | Admin panel requires two-factor authentication. |
| SEC-07 | Secrets (API keys, database passwords) stored only on the server, never in the mobile app. |
| SEC-08 | Rate limiting on login, OTP, and chatbot endpoints. |
| SEC-09 | Input validation on every API endpoint. |
| SEC-10 | Chatbot protected against prompt injection: it can only read data, never write; it sees only the current student's data. |
| SEC-11 | Dependency and vulnerability scanning in the build pipeline. |
| SEC-12 | Security testing (OWASP Mobile Top 10 and API Top 10 checklist) before launch. |

## 6. Privacy

| ID | Requirement |
|---|---|
| PRIV-01 | Collect only data needed for recommendations. Sensitive optional fields (disability, minority status) are opt-in and explained. |
| PRIV-02 | Clear privacy policy in simple English (and Urdu later). |
| PRIV-03 | Student consent recorded at sign-up with policy version and date. |
| PRIV-04 | Students can view, export, correct, and delete their data. |
| PRIV-05 | Personal data is not sent to the AI provider unless needed for the question; names, phone numbers, and emails are never sent. |
| PRIV-06 | Choose AI and hosting providers that do not train on our data and that offer clear data retention terms. |
| PRIV-07 | Follow Pakistan's applicable laws: the Prevention of Electronic Crimes Act (PECA) 2016 and the Personal Data Protection law/bill. **The data protection law's current status must be checked with a legal advisor before launch** (it has been in draft form for several years). Also follow Google Play and Apple App Store data rules. |
| PRIV-08 | Users under 18: show a parent/guardian notice; avoid collecting more than needed. |
| PRIV-09 | Analytics never contain marks, names, or contact details. |

## 7. Usability

| ID | Requirement |
|---|---|
| USE-01 | Simple English, short sentences. Urdu support planned (design all text for translation from day 1). |
| USE-02 | Profile setup can be completed in under 5 minutes, split into small steps with progress saved. |
| USE-03 | Works well on small screens (5 inch) and large phones; tablet support basic. |
| USE-04 | Accessibility: text scales with phone settings, minimum touch target 48dp, colour is never the only signal (icons + text for eligibility status), screen-reader labels. |
| USE-05 | Light and dark mode. |
| USE-06 | Every error message tells the user what to do next. |

## 8. Maintainability

| ID | Requirement |
|---|---|
| MAINT-01 | Clean, modular code: feature-based folders in Flutter; separate modules for auth, profile, catalogue, eligibility, chat, admin in the backend. |
| MAINT-02 | Eligibility rules stored as data with a versioned schema, not hard-coded. |
| MAINT-03 | Automated tests: unit tests for the engine (high coverage), widget tests for key screens, API integration tests. |
| MAINT-04 | CI pipeline runs tests and linting on every change. |
| MAINT-05 | Separate environments: development, staging, production. |
| MAINT-06 | API versioning (`/v1/...`) so old app versions keep working. |
| MAINT-07 | Documentation kept in this `docs/` folder and updated with each phase. |

## 9. Cost

| ID | Requirement |
|---|---|
| COST-01 | MVP hosting + AI cost target: under about USD 100/month at 10,000 students (to be confirmed with real usage). |
| COST-02 | Chatbot cost controls: daily message limit, answer caching for common questions, prompt caching, cheaper model for simple questions if quality holds. |
| COST-03 | Avoid services with high fixed monthly costs during the MVP. |

## 10. Compatibility

| ID | Requirement |
|---|---|
| COMP-01 | Android 8.0 (API 26) and newer for MVP. |
| COMP-02 | iOS 15+ when iOS is released (needs an Apple developer account and a Mac for builds). |
| COMP-03 | Admin panel works on latest Chrome, Edge, and Firefox on desktop. |

## 11. Observability

| ID | Requirement |
|---|---|
| OBS-01 | Crash reporting in the mobile app. |
| OBS-02 | Server error logging and alerting. |
| OBS-03 | Chatbot logs (question, retrieved sources, answer, rating) kept for quality review, with personal data removed, for a limited time (e.g., 90 days). |
