# Admin Panel Plan

## 1. Decision: separate web application

The admin panel should be a **separate web app** used on a laptop/desktop, talking to the same FastAPI backend.

**Why separate:**
- Data entry (long prospectus tables, rule builders, PDF side-by-side) needs a big screen.
- Keeps admin features and permissions completely out of the student app (smaller attack surface).
- Can be released and updated independently.

**Technology:** React (Next.js) + an admin framework such as Refine, **or** Flutter Web if the team knows only Dart. See [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md#24-admin-panel).

**Access:** Only staff accounts with an admin role; two-factor authentication required.

---

## 2. Roles and permissions

| Action | Data Editor | Data Verifier | Support | Super Admin |
|---|---|---|---|---|
| Create/edit draft catalogue data | ✅ | ✅ | ❌ | ✅ |
| Verify/publish data | ❌ (not own edits) | ✅ (not own edits) | ❌ | ✅ |
| Manage reference lists (boards, subjects, groups) | Draft | ✅ | ❌ | ✅ |
| Manage KB articles (app help, guides) | ✅ | ✅ (publish) | ✅ (draft) | ✅ |
| Review student error reports | ✅ | ✅ | ✅ | ✅ |
| Review chatbot feedback | ❌ | ✅ | ✅ | ✅ |
| View student accounts (limited fields) | ❌ | ❌ | ✅ | ✅ |
| Disable/delete student accounts | ❌ | ❌ | Request | ✅ |
| Manage admin users and roles | ❌ | ❌ | ❌ | ✅ |
| View audit log | ❌ | ❌ | ❌ | ✅ |
| Change ranking weights / chatbot settings | ❌ | ❌ | ❌ | ✅ |

**Four-eyes rule:** a person cannot verify their own changes.

---

## 3. Main sections

### 3.1 Dashboard
- Data coverage: universities / campuses / programmes / offerings for current cycle — by status (draft, pending, verified, published).
- **Stale data**: offerings still using last cycle's data; sources not checked in X days; broken links found by the link checker.
- Review queues: pending verifications, student reports, chatbot 👎.
- Upcoming deadlines in the next 30 days.
- Usage: active students, recommendation runs, top searched programmes, chat questions without answers.

### 3.2 Universities, campuses, programmes
- List with search, filters (province, sector, status), and bulk actions.
- University form: names, aliases, sector, HEC status, gender policy, links, logo.
- Campus form: city, address, map pin, gender policy, hostels.
- Programme form: discipline, title as written by the university, degree type, duration, shift, accreditation.

### 3.3 Offerings (per admission cycle)
- "Copy from previous cycle" button → creates drafts.
- Tabs per offering: **Rules · Fees · Entry tests · Deadlines · Quotas · Seats · Notes · Sources**.
- Side-by-side view: PDF prospectus page on the left, form on the right.

**PDF FR-03 coverage:**
| FR-03 bullet | Where |
|---|---|
| Add and update university profiles | 3.2 |
| Maintain courses, durations, fees, locations | 3.2 (programmes, campuses), 3.3 (offerings), 3.5 (fees) |
| Record admission requirements and official links | 3.4 (rule builder), 3.2 (official website and admission URLs) |
| Update outdated records and mark unavailable offerings | 3.3: "Not offered this cycle" switch (offering stays in history, never shown in recommendations); 3.1: stale-data list; 3.9: re-verification workflow |

### 3.4 Eligibility rule builder (no code)
- Add rule set → name it ("For ICS students").
- Add rules from a menu of rule types; each type shows a simple form:
  - *Accepted backgrounds:* tick boxes for levels/types/groups.
  - *Required subjects:* "must have all of" chips + "must have one of" groups.
  - *Minimum percentage:* level + number.
  - *Entry test:* pick tests + optional minimum.
  - *Gender / age / passing year / deficiency course / IBCC / interview note.*
- Each rule needs a **source** (prospectus page or URL).
- Live preview of how the rule reads to students ("Your FSc Pre-Engineering background is accepted...").
- **Test panel:** pick sample profiles (or enter one) and see the result instantly.
- **Impact preview before publishing:** "This change moves 3 golden-test profiles from Eligible to Not eligible" + list.

### 3.5 Fees
- Add fee components (admission, tuition, registration, exam, lab, security, other) with basis (one-time, per semester, per year, per credit hour).
- Auto-calculated totals shown: tuition per semester, first semester total, first year total, degree estimate.
- Flag "estimated" values.

### 3.6 Hostels
- Per campus: boys/girls, on/off campus, availability, capacity, fees per cycle, notes.

### 3.7 Reference data
- Regions, districts, cities, boards, qualification types, groups, subjects, default subject combinations, programme fields, disciplines, entry tests, accreditation bodies, admission cycles.

### 3.8 Sources and documents
- Upload prospectus PDFs; store the original URL.
- Record retrieved date and content hash.
- Link checker results (link broken / page changed since last verification).

### 3.9 Verification workflow
```
Draft ──(editor submits)──► Pending review ──(verifier approves)──► Verified ──(publish)──► Published
   ▲                              │
   └──────(verifier rejects with comment)
```
- Verifier sees a **diff** (old vs new values) and the source side by side.
- "Publish" creates a new data version, refreshes the search view, engine cache, and chatbot admissions cards.

### 3.10 Review queues
- **Student error reports:** see report, linked record, screenshot; assign; fix; reply to student.
- **Chatbot feedback:** question, retrieved sources, answer, rating; mark as "wrong data", "retrieval problem", "model problem", "OK"; create KB article or data fix from it.
- **Unanswered questions:** questions where the bot said "I don't have verified information" → ideas for new content.

### 3.11 Knowledge base
- Write/edit app-help and guide articles (Markdown editor with preview).
- Status: draft → published. Publishing re-indexes the article.
- View chunks and test search ("what would the bot find for this question?").

### 3.12 Students
- Search by email/phone (support role).
- View limited info: account status, created date, profile completion. **Marks and sensitive fields hidden** by default; viewing them requires a reason and is logged.
- Actions: resend verification, disable account, process deletion requests.

### 3.13 Settings (super admin)
- Ranking weights, chatbot daily limit, model selection, feature flags, current admission cycle.
- Admin users and roles.
- Audit log viewer.

---

## 4. Data collection process (people + tools)

Collecting data is the **biggest ongoing task**. Suggested process:

1. **Master list** of universities from the HEC recognised list. Add campuses.
2. **Prioritise** the pilot set (see roadmap).
3. For each university each cycle:
   - Download the official prospectus/admission notice → upload as a source.
   - Enter offerings, rules, fees, tests, deadlines, hostels with page references.
   - A second person verifies against the source.
4. **Programme accreditation** cross-checked with official body lists (PEC for engineering, PM&DC for medical/dental, NCEAC for computing, NBEAC for business, etc.).
5. **Monitoring:** weekly automatic link/page-change checks; admission-season calendar reminders to re-verify.
6. **Student reports** feed corrections.
7. Later: contact university admission offices to confirm data or allow them to suggest corrections (reviewed by us).

**Tools to speed up entry (later):** AI-assisted extraction from prospectus PDFs that **pre-fills drafts only**. A human must check and verify every field. AI-extracted values are labelled until verified.

---

## 5. Admin panel MVP scope

Must-have: login + 2FA, roles, reference data, universities/campuses/programmes/offerings, rule builder with test panel, fees, hostels, tests, deadlines, sources, verification workflow, publish, audit log, student report queue, KB articles.

Later: impact preview against the golden set, AI-assisted PDF extraction, link-change detector dashboard, analytics, university-partner accounts.
