# Project Overview

> Working name: **UniRah** (placeholder — "Rah" means "path". Change it any time.)
> Status: **Planning — not approved for implementation yet.**
> Date: 18 November 2026

---

## 1. What are we building?

A mobile app (Android first, iOS later) that works like a **university counsellor in the student's pocket** for students in Pakistan.

A student:

1. Creates an account.
2. Enters their education history (Matric, Intermediate, A-Levels, DAE, etc.) with subjects and marks.
3. Sets their preferences (provinces, cities, budget, sector, hostel, degree fields).
4. Gets a list of universities and programmes, sorted into three groups:
   - **Eligible** — meets all the published requirements we can check.
   - **Potentially Eligible** — may qualify, but something must still be checked or done.
   - **Not Currently Eligible** — fails at least one known requirement.
5. Sees **why** each result was given, with a link to the official source.
6. Can ask an AI assistant questions about the app and about admissions. The assistant only answers from verified information.

### Baseline document
The file `Student_Recommendation_Workflow_and_Requirements-1.pdf` (project folder) is the **baseline**: its workflow (Student Input → Matching & Ranking → Results & Decision) and requirements FR-01 to FR-06 must all be met. These planning documents extend it. The mapping is in [FUNCTIONAL_REQUIREMENTS.md § 0](FUNCTIONAL_REQUIREMENTS.md#0-baseline-workflow-pdf-fr-01-to-fr-06) and the corrected workflow diagram is in [RECOMMENDATION_ENGINE.md § 0](RECOMMENDATION_ENGINE.md#0-end-to-end-workflow-aligned-with-the-workflow-pdf).

**The PDF is a fixed required specification (confirmed).** Version 1.0 delivers it in full. The AI assistant and notifications are **extensions** planned for version 1.1. Data details that make eligibility correct (subjects per stream, result status, entry tests, gender policy, hostels) stay in version 1.0 because FR-02 to FR-05 need them. Changes to the PDF's workflow diagram are listed in [CHANGE_REQUEST_FOR_SUPERVISOR.md](CHANGE_REQUEST_FOR_SUPERVISOR.md) and wait for approval.

## 2. Who is it for?

| User | What they need |
|---|---|
| **Students** (age ~16–22) finishing Matric/Inter/A-Levels/DAE | Find programmes they can actually apply to, within their budget and region |
| **Parents** | Understand fees, hostel options, safety, and the difference between public and private universities |
| **Data administrators** (our team) | Add and update university data quickly and correctly |
| **Super admin** (project owner) | Control users, roles, data quality, and the AI assistant |

Later (not in version 1): school/college counsellors, and possibly university admission offices who want to correct their own data.

## 3. The problem we solve

- Admission rules are spread across hundreds of websites and PDF prospectuses.
- Rules differ by **programme**, **campus**, **year**, and **the student's background** (for example, ICS students and Pre-Medical students have different options for BS Computer Science).
- Many students do not know about **deficiency courses**, **IBCC equivalence** for A-Levels, **entry tests** (ECAT, MDCAT, NAT, university tests), or **quota seats**.
- Fee information is hard to compare because universities show fees per semester, per year, or per credit hour.
- Students often get advice from unreliable social media posts.

## 4. Core principles

1. **Verified data first.** Every eligibility rule and fee shown must link to an official source and show when it was last checked.
2. **Eligibility is not admission.** The app says "you meet the minimum published requirements". It never says "you will get admission".
3. **Explain everything.** Each result has a clear, human reason.
4. **Rules are data, not code.** New provinces, universities, programmes, and rules are added through the admin panel without changing app code.
5. **AI explains; it does not decide.** The eligibility result comes from a fixed rule engine. The AI assistant can explain results but cannot change them or invent rules.
6. **Start small, be correct.** A smaller, accurate version 1 is better than a big, wrong one.

## 5. Objectives

### Version 1 (MVP) objectives
- Student accounts and complete academic profiles that match Pakistan's education system.
- A rule-based eligibility engine with three result categories and explanations.
- Verified data for a **pilot set** of universities and programme families (proposed: ~40–60 universities, focused on Computing, Engineering, Business, and Medical/Allied Health — see the roadmap).
- Search and filters (province, city, sector, fee range, hostel, gender policy, degree field).
- University and programme detail pages with official links and "last verified" dates.
- Shortlist (save) universities and compare options.
- Clear no-match handling with suggestions.
- Web admin panel for data entry, verification, and review.

### Version 1.1 objectives
- AI help assistant (app support + admissions information) using RAG with citations.
- Deadline reminders and data-change notifications.

### Later objectives
- All HEC-recognised universities and campuses.
- Merit/aggregate calculator (formula per university).
- Deadline reminders and push notifications.
- Scholarships and financial aid.
- Urdu language support.
- Past merit lists (shown as history only, never as a prediction).

## 6. Success measures

| Measure | Target for MVP |
|---|---|
| Eligibility accuracy (checked against hand-reviewed test cases) | 98%+ match with expert review |
| Records with an official source link and verification date | 100% |
| Records older than one admission cycle shown without a warning | 0 |
| Chatbot answers that include a source when talking about admissions (v1.1) | 95%+ |
| Chatbot answers that contain made-up rules, found in review (v1.1) | Close to 0; each case fixed |
| Profile completion rate after sign-up | 60%+ |
| App crash-free sessions | 99%+ |

## 7. What is out of scope for version 1

- Applying to universities through our app (we only link to official portals).
- Online payment of university fees.
- Predicting the chance of admission.
- Postgraduate (MS/MPhil/PhD) programmes.
- Foreign universities.
- Live chat with human counsellors.

## 8. Related documents

| Document | Purpose |
|---|---|
| [FUNCTIONAL_REQUIREMENTS.md](FUNCTIONAL_REQUIREMENTS.md) | What the system must do |
| [NON_FUNCTIONAL_REQUIREMENTS.md](NON_FUNCTIONAL_REQUIREMENTS.md) | Speed, security, reliability, usability |
| [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) | Technology choices and how parts connect |
| [DATABASE_DESIGN.md](DATABASE_DESIGN.md) | Tables and relationships |
| [RECOMMENDATION_ENGINE.md](RECOMMENDATION_ENGINE.md) | Eligibility and ranking logic |
| [RAG_CHATBOT_ARCHITECTURE.md](RAG_CHATBOT_ARCHITECTURE.md) | AI assistant design |
| [UI_UX_PLAN.md](UI_UX_PLAN.md) | Screens and user journeys |
| [ADMIN_PANEL_PLAN.md](ADMIN_PANEL_PLAN.md) | Data management tools |
| [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) | Phases and timeline |
| [RISKS_AND_CHALLENGES.md](RISKS_AND_CHALLENGES.md) | Risks and how we handle them |
| [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) | Decisions we need from the project owner |
