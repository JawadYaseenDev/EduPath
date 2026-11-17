# Functional Requirements

Each requirement has an ID, a priority, and a short description.

**Priority:** `M` = Must have (MVP) · `S` = Should have (MVP if time allows) · `L` = Later version

Items marked **[NEW]** were not in the original brief. They are suggestions found during analysis.

---

## 0. Baseline: Workflow PDF (FR-01 to FR-06)

The file `Student_Recommendation_Workflow_and_Requirements-1.pdf` (in the project folder) defines six baseline requirements and the main student workflow. **Every baseline requirement is covered below.** This document adds detail and closes gaps; it does not remove anything from the PDF.

### 0.1 Traceability table

| PDF requirement | PDF bullet points | Covered by (this document) |
|---|---|---|
| **FR-01** User Registration and Authentication | Register with email + password; validate details; show errors for invalid input; redirect to dashboard; clear session on logout | AUTH-01, AUTH-02, AUTH-05, AUTH-06, AUTH-10, AUTH-11 |
| **FR-02** Student Profile and Preferences Management | Enter qualifications, subjects, marks/grades; select interests and fields; set budget and location; validate and save | PROF-01 – PROF-32, PREF-01 – PREF-15 |
| **FR-03** Course and University Information Management (admin) | Add/update universities; maintain courses, durations, fees, locations; record admission requirements and official links; update outdated records and mark unavailable offerings | ADM-01 – ADM-13 (+ [ADMIN_PANEL_PLAN.md](ADMIN_PANEL_PLAN.md)) |
| **FR-04** Eligibility Checking and Personalised Recommendations | Compare qualifications/subjects/marks with requirements; apply budget and location; rank eligible options by fit; explain why; no-match message and preference change | REC-01 – REC-08, REC-15, REC-16 (+ [RECOMMENDATION_ENGINE.md](RECOMMENDATION_ENGINE.md)) |
| **FR-05** Search, Filtering and Comparison | Search by course/university name; filter by field, location, fee; view details; compare fees, duration, location, requirements | SRCH-01 – SRCH-04, REC-09 |
| **FR-06** Shortlist and Admission Guidance | Add to shortlist; view/remove; review requirements for shortlisted offerings; open official admission pages | REC-10, SHORT-01 – SHORT-03, NOTIF-01 – NOTIF-04 |

### 0.2 Rules taken from the PDF (must not be broken)

| ID | Rule |
|---|---|
| BASE-01 | **Rank only eligible offerings. Never relax academic eligibility** to produce more results. Preferences change sorting and visibility only. |
| BASE-02 | **Recommendations support decisions; they do not guarantee admission.** This message appears on results and detail screens. |
| BASE-03 | Profile data stays editable at any time. Invalid inputs show clear error messages. |
| BASE-04 | When no option matches, show an explanation and let the student change their inputs and search again. |
| BASE-05 | Eligibility is marks-based and rules-based, using curated (admin-maintained) institutional data. Ranking is transparent. |

### 0.3 Gaps in the PDF and how this plan closes them

| Gap in the PDF | How we close it |
|---|---|
| Only two outcomes (eligible / not). No place for uncertain cases (result awaited, A-Level without IBCC certificate, missing data, interview required). | Added a third group, **Potentially Eligible** (REC-01). It does not relax eligibility: no **known** requirement is failed, but at least one cannot be confirmed yet. It is shown separately and labelled clearly, so BASE-01 still holds. |
| One "no match" path for two different problems. A student who fails **academically** cannot fix it by changing budget or location. | Two separate no-match paths: **academic no-match** (explain and suggest other fields, deficiency-course routes, entry tests) and **preference no-match** (suggest which preference to relax). See REC-15, REC-16. |
| The revise loop only goes back to preferences. | Changing academic data re-runs the eligibility check. Changing preferences only re-runs ranking (PROF-32, REC-17). |
| FR-01 has no email verification, password reset, or account deletion. | AUTH-02, AUTH-05, AUTH-07. |
| FR-02 does not describe stream-specific subjects, separate Matric/Inter records, or result status. | PROF-10 – PROF-16. |
| FR-03 has no source, verification date, admission year, or review step. | ADM-04, ADM-05, ADM-11, ADM-13; offerings are stored per admission cycle. |
| FR-04 "explain why" is not defined. | One plain-language reason per rule, with the official source and date (REC-04). |
| No non-functional requirements. | [NON_FUNCTIONAL_REQUIREMENTS.md](NON_FUNCTIONAL_REQUIREMENTS.md). |

---

## 1. Accounts and Authentication (AUTH)

| ID | Priority | Requirement |
|---|---|---|
| AUTH-01 | M | Student can sign up with email + password. |
| AUTH-02 | M | Email must be verified before recommendations are shown. |
| AUTH-03 | S | Sign in with Google. |
| AUTH-04 | S | Phone number sign-up with SMS OTP. **[NEW]** Many students use phone more than email. SMS has a cost per message — see open questions. |
| AUTH-05 | M | Forgot password / reset password. |
| AUTH-06 | M | Student can log out from all devices. |
| AUTH-07 | M | Student can delete their account and all personal data. **[NEW]** Needed for privacy and Google Play policy. |
| AUTH-08 | M | Student can download a copy of their data. **[NEW]** |
| AUTH-09 | S | Guest mode: browse universities without an account; recommendations need an account. **[NEW]** Lowers the barrier to first use. |
| AUTH-10 | M | Registration and login inputs are validated; clear error messages are shown (e.g., "Email already registered", "Wrong email or password"). *(PDF FR-01)* |
| AUTH-11 | M | After login, the student goes to the **dashboard** (Home). Students without a complete profile go to the profile wizard first. Logout clears the session and stored tokens on the device. *(PDF FR-01)* |

## 2. Student Profile (PROF)

### 2.1 Personal information
| ID | Priority | Requirement |
|---|---|---|
| PROF-01 | M | Full name, email, phone, gender, date of birth **[NEW — some programmes have age limits]**, current city, province / region of domicile. |
| PROF-02 | M | **Domicile** (province/district) stored separately from current city. **[NEW]** Many public universities have regional quota seats based on domicile, not current address. |
| PROF-03 | S | Special categories the student can choose to share (optional): disabled-person quota, Hafiz-e-Quran, sports, children of employees, minority, overseas Pakistani. **[NEW]** These change eligibility or add marks at some universities. Always optional. |

### 2.2 Education history
| ID | Priority | Requirement |
|---|---|---|
| PROF-10 | M | Student adds **one record per qualification**: Secondary (Matric / O-Levels / equivalent) and Higher Secondary (Intermediate / A-Levels / DAE / equivalent). |
| PROF-11 | M | For each record: qualification type, group/stream, board or examining body, passing year, obtained marks, total marks, and auto-calculated percentage. |
| PROF-12 | M | Subjects are selected from a list that depends on the chosen group (e.g., ICS shows Maths, Computer Science, Physics **or** Statistics). The student can correct subjects if their combination is different. |
| PROF-13 | M | **Result status**: "Result announced", "Part-I only (result awaited)", "Appearing / not yet appeared". **[NEW]** Most students apply before the final Inter result. Many universities accept Part-I marks. |
| PROF-14 | M | Subject-wise marks are optional but supported. **[NEW]** Some programmes need minimum marks in a specific subject (e.g., Maths). |
| PROF-15 | M | A-Levels: grades per subject + **IBCC equivalence** percentage (entered by student or estimated with a clear label). **[NEW]** |
| PROF-16 | M | DAE: technology/discipline (e.g., Electrical, Civil, Computer Information Technology). **[NEW]** DAE students usually go to BSc Engineering Technology or some BS programmes. |
| PROF-17 | S | Entry test results: test name (ECAT, MDCAT, NAT, NET, SAT, university test), score, total, year. **[NEW]** |
| PROF-18 | S | "Improvement of marks" / supplementary exam flag. **[NEW]** Some universities deduct marks or reject improved results. |
| PROF-19 | M | Qualification types, groups, subjects, and boards are managed as data in the admin panel, so new ones can be added without app updates. |

### 2.3 Profile rules
| ID | Priority | Requirement |
|---|---|---|
| PROF-30 | M | Obtained marks cannot be more than total marks; percentage is calculated, not typed. |
| PROF-31 | M | Profile completion indicator showing what is missing. |
| PROF-32 | M | Any profile change marks old recommendations as "out of date" and offers a refresh. |

## 3. Preferences (PREF)

| ID | Priority | Requirement |
|---|---|---|
| PREF-01 | M | Select one or more provinces/regions (Punjab, Sindh, KP, Balochistan, Gilgit-Baltistan, ICT, **Azad Jammu & Kashmir [NEW]**). |
| PREF-02 | S | Select specific cities, or "within X km of my city". **[NEW]** |
| PREF-03 | M | Budget: **maximum amount per semester** using a slider or number input, instead of fixed ranges. Fixed ranges are shown as quick-pick chips. |
| PREF-04 | M | Choose what the budget includes: tuition only / tuition + other university charges / tuition + hostel. |
| PREF-05 | S | Show first-year total cost (admission fee + 2 semesters + hostel) as a separate figure. **[NEW]** The first semester is often much more expensive. |
| PREF-06 | M | Sector: Public, Private, Semi-government / Armed-forces-run (multi-select). |
| PREF-07 | M | Hostel need: Not needed / Needed / Needed on-campus only. |
| PREF-08 | M | Gender-based options: show only co-education, only women's universities/campuses, or both. Gender policy of each campus is always respected in eligibility. |
| PREF-09 | M | Degree fields: choose broad fields (e.g., Computing) and/or specific programmes (e.g., BS Artificial Intelligence). |
| PREF-10 | S | Shift: Morning / Evening / Weekend. **[NEW]** Evening programmes are often cheaper or have lower merit. |
| PREF-11 | S | Programme accreditation required: e.g., only PEC-accredited engineering, PM&DC-recognised medical colleges, NCEAC-accredited computing. **[NEW]** Very important for engineering and medical students. |
| PREF-12 | S | Entry test willingness: "I can take ECAT / MDCAT / NAT / university tests". **[NEW]** |
| PREF-13 | L | Scholarship / need-based aid needed. **[NEW]** |
| PREF-14 | L | Transport available. **[NEW]** |
| PREF-15 | M | Preferences are **soft filters**: results outside preferences are hidden by default but can be shown with one tap ("Show 12 more outside your budget"). |

## 4. Recommendations (REC)

| ID | Priority | Requirement |
|---|---|---|
| REC-01 | M | Generate results grouped as **Eligible**, **Potentially Eligible**, **Not Currently Eligible**. |
| REC-02 | M | Each result is for a **programme at a specific campus for a specific admission year** (not just a university). |
| REC-03 | M | Each result shows: university, campus, city, province, programme, sector, eligibility status, minimum criteria, fee summary, entry test, hostel availability, official website, official admission page, last verified date. |
| REC-04 | M | Each result shows **reasons** in plain language, one line per rule checked (passed / failed / unknown). |
| REC-05 | M | "Not Currently Eligible" shows what is missing and, where the rules allow, what the student can do (e.g., "Take the deficiency Maths course"). |
| REC-06 | M | A permanent notice: "Meeting minimum eligibility does not guarantee admission. Admission depends on merit, seats, and the university's final decision." |
| REC-07 | M | Results inside a group are sorted by how well they match preferences (see RECOMMENDATION_ENGINE.md). Student can re-sort by fee, distance, name. |
| REC-08 | M | Results based on data older than the current admission cycle show a warning badge: "Data from 2025 cycle — check the official site". |
| REC-09 | S | Compare up to 3 programmes side by side. **[NEW]** |
| REC-10 | M | Save/shortlist programmes. |
| REC-11 | S | Share a result as an image or link (no personal data in the link). **[NEW]** |
| REC-12 | M | "Report incorrect information" button on every university and programme. **[NEW]** Feeds the admin review queue. |
| REC-13 | L | Merit/aggregate calculator using the university's published formula (e.g., Matric 10% + Inter 40% + Test 50%). Shown as "your calculated aggregate", never as a chance of admission. **[NEW]** |
| REC-14 | L | Past closing merit for reference only, with a clear "history, not a prediction" label. **[NEW]** |
| REC-15 | M | **Academic no-match:** if the student is not eligible (or potentially eligible) for **any** programme in their chosen fields, show why (the most common failed rules) and suggest: related fields that accept their background, deficiency-course routes, and programmes that need an entry test. Do **not** suggest changing budget or location, because that cannot help. *(Closes a gap in PDF FR-04.)* |
| REC-16 | M | **Preference no-match:** if eligible options exist but none fit the preferences, show how many options each change would unlock (e.g., "Raise budget to PKR 80,000 → 6 more options", "Add Sindh → 4 more options") and let the student change preferences in one tap. *(PDF FR-04)* |
| REC-17 | M | After the student changes **academic data**, eligibility is checked again. After the student changes **only preferences**, the saved eligibility is reused and only filtering and ranking run again. |

## 5. Search and Browse (SRCH)

| ID | Priority | Requirement |
|---|---|---|
| SRCH-01 | M | Search universities and programmes by name (with spelling tolerance, e.g., "comsats", "COMSATS University"). |
| SRCH-02 | M | Filter by province, city, sector, programme field, fee range, hostel, gender policy, entry test, accreditation. |
| SRCH-03 | M | University detail page: overview, campuses, programmes, fees, hostels, contact, official links, verification date. |
| SRCH-04 | M | Programme detail page: eligibility rules, required subjects, minimum marks, entry test, fee breakdown, seats (if published), deadlines, official links. |
| SRCH-05 | S | Map view of campuses. |

## 5a. Shortlist (SHORT)

| ID | Priority | Requirement |
|---|---|---|
| SHORT-01 | M | Add or remove programmes (and universities) from a personal shortlist from any list or detail screen. *(PDF FR-06)* |
| SHORT-02 | M | The shortlist screen shows each saved option with its eligibility status, admission requirements, fees, and next deadline. *(PDF FR-06)* |
| SHORT-03 | M | Each shortlisted option has an "Open official admission page" button. *(PDF FR-06)* |

## 6. Deadlines and Notifications (NOTIF) **[NEW section]**

> **Version 1.1**, except NOTIF-01 (showing deadline dates on detail screens), which stays in version 1.0 as part of FR-06 admission guidance.

| ID | Priority | Requirement |
|---|---|---|
| NOTIF-01 | S | Show admission open/close dates and entry test dates where available. |
| NOTIF-02 | S | Push reminder before the deadline of a shortlisted programme (e.g., 7 days and 1 day). |
| NOTIF-03 | S | Notify when data for a shortlisted programme changes (e.g., new fee, new deadline). |
| NOTIF-04 | M | Student controls all notification settings. |

## 7. AI Assistant (CHAT)

> **Version 1.1.** Not in the baseline PDF. "M" below means must-have *for version 1.1*.

| ID | Priority | Requirement |
|---|---|---|
| CHAT-01 | M | Chat screen available from every main screen. |
| CHAT-02 | M | Answers **app-help** questions (how to use features, fix profile issues). |
| CHAT-03 | M | Answers **admissions** questions using only the verified knowledge base, with source links and dates. |
| CHAT-04 | M | Can explain the student's **own** recommendation results by reading the stored engine output — it cannot change the result. |
| CHAT-05 | M | When information is not in the knowledge base, it says so clearly and points to the official website. |
| CHAT-06 | M | Thumbs up/down + "report wrong answer" on every reply. |
| CHAT-07 | M | Suggested starter questions. |
| CHAT-08 | S | Understands Roman Urdu questions (e.g., "mujhe kaun si university mil sakti hai?"). **[NEW]** |
| CHAT-09 | M | Daily message limit per student to control cost. |
| CHAT-10 | M | Refuses unrelated or harmful requests politely. |
| CHAT-11 | S | Can open app screens (e.g., "Open my preferences") through action buttons. |

## 8. Admin Panel (ADM) — summary

Full detail in [ADMIN_PANEL_PLAN.md](ADMIN_PANEL_PLAN.md).

| ID | Priority | Requirement |
|---|---|---|
| ADM-01 | M | Manage universities, campuses, programmes, offerings per admission year. |
| ADM-02 | M | Manage eligibility rules with a form-based rule builder (no code). |
| ADM-03 | M | Manage fees, hostels, entry tests, deadlines. |
| ADM-04 | M | Every record has a source link, source document upload, and verification status. |
| ADM-05 | M | Two-person check: one admin enters, another verifies, before data goes live. |
| ADM-06 | M | Change history for every record. |
| ADM-07 | M | Review queue for student error reports and chatbot feedback. |
| ADM-08 | M | Manage the chatbot knowledge base (FAQ, help articles) and re-index it. |
| ADM-09 | M | Role-based access (Super Admin, Data Editor, Data Verifier, Support). |
| ADM-10 | S | Test the engine: enter a sample student profile and see results before publishing rule changes. |
| ADM-11 | S | Stale data dashboard: records not verified in this admission cycle. |
| ADM-12 | M | Manage student accounts (view limited info, disable, delete on request). |
| ADM-13 | M | Mark an offering as **not offered this cycle** (unavailable) without deleting it, and flag records as **outdated** when they belong to an older admission cycle or their source has changed. Unavailable offerings never appear in recommendations. *(PDF FR-03)* |

## 9. Content and Guidance (GUIDE) **[NEW section]**

| ID | Priority | Requirement |
|---|---|---|
| GUIDE-01 | S | Short guides: "What is ECAT?", "What is MDCAT?", "What is IBCC equivalence?", "Public vs private universities", "What is a deficiency course?". |
| GUIDE-02 | S | Glossary of admission terms. |
| GUIDE-03 | M | These guides are also used by the chatbot as knowledge. |

## 10. Feedback and Analytics (ANL)

| ID | Priority | Requirement |
|---|---|---|
| ANL-01 | M | Anonymous usage analytics (screens used, recommendation runs) without storing marks in analytics tools. |
| ANL-02 | S | Admin dashboard: most-searched programmes, most-reported errors, chatbot questions with no answer. |
