# UI / UX Plan

## 1. Design principles

1. **Small steps.** Long forms are split into short screens with progress saved after each step.
2. **Clear status.** Eligibility uses **icon + colour + word** (✅ Eligible, 🟡 Potentially Eligible, 🔴 Not Currently Eligible) — never colour alone.
3. **Show the source.** Every fact on detail screens has "Source · Verified on [date]".
4. **Honest wording.** "Meets minimum requirements" — never "You will get in".
5. **Friendly for first-time smartphone users and parents.** Big touch targets, simple words, no jargon without a tooltip.
6. **Translation-ready.** All text in translation files; layouts tested with longer text and right-to-left (for Urdu later).
7. **Works on weak internet.** Skeleton loaders, cached lists, retry buttons, forms never lose input.

## 2. Navigation structure

Bottom navigation with 4 tabs + a floating chat button (the chat button arrives in version 1.1):

```
┌────────────────────────────────────────────┐
│  Home  │  Explore  │  Shortlist  │ Profile │   + 💬 Chat (floating, all main tabs)
└────────────────────────────────────────────┘
```

| Tab | Purpose |
|---|---|
| **Home** (the dashboard in PDF FR-01) | Recommendation summary, next deadlines, profile completion, tips. Students land here after login. |
| **Explore** | Search and filter all universities/programmes (works without profile) |
| **Shortlist** | Saved programmes, compare, deadlines |
| **Profile** | Education, preferences, test scores, settings, privacy |

## 3. Screen list

### 3.1 Onboarding and auth
| # | Screen | Notes |
|---|---|---|
| 1 | Splash | Logo, checks session |
| 2 | Welcome carousel (3 slides) | What the app does; "Eligibility ≠ admission" message; skip button |
| 3 | Sign up | Email + password, or Google; phone OTP later. Link to privacy policy; consent checkbox |
| 4 | Sign in | |
| 5 | Verify email | Resend button, "open email app" |
| 6 | Forgot / reset password | |
| 7 | Continue as guest (optional) | Explore only |

### 3.2 Profile setup wizard (first time)
Progress bar: **Step X of 6**. Each step saves on "Next".

| Step | Screen | Content |
|---|---|---|
| 1 | About you | Name, gender, date of birth, phone (optional), current city, domicile district |
| 2 | Secondary (Matric/O-Level) | Type → group → board → year → marks (obtained/total) → auto percentage; subject chips pre-filled from group, editable |
| 3 | Higher Secondary (Inter/A-Level/DAE) | Same pattern + result status (Final / Part-I only / Not yet appeared) + Part-I marks if needed; A-Level: subjects + grades + IBCC equivalence; DAE: discipline |
| 4 | Entry tests (optional) | Add test, score, year — "Skip for now" |
| 5 | Interests | Pick fields (cards with icons) → then specific programmes (chips) |
| 6 | Preferences | Provinces (multi-select chips), cities (optional), budget slider + "includes hostel?" toggle, sector, hostel need, campus type, shift, accreditation toggle |
| ✓ | Review | Summary with "Edit" per section → **"Find my universities"** button |

Helpful details:
- Board list filtered by province first, with search.
- "Why do we ask this?" info icon on sensitive fields (gender, domicile, special categories).
- Validation messages in plain words: "Obtained marks cannot be more than total marks."

### 3.3 Recommendations
| Screen | Content |
|---|---|
| **Results summary** | Three tappable cards: ✅ Eligible (count), 🟡 Potentially (count), 🔴 Not currently (count). Notice: "Based on data verified for Fall 2027. Meeting the minimum does not guarantee admission." "Update results" if profile changed |
| **Results list (per category)** | Cards: university logo, programme, campus + city, sector badge, fee per semester, hostel icon, entry test chip, "Data from 2026" badge if stale. Sort (best match, fee low→high, distance, name). Filter chips. "Show N more outside your preferences" at the bottom |
| **Result detail / Why?** | Status banner; checklist of rules with ✅ / ❌ / ❔ and plain reasons; "What to do next" list; fee breakdown; hostel info; deadlines; source + verified date; buttons: Save, Compare, Official admission page, Ask assistant about this, Report incorrect info |
| **Alternatives** (for not eligible) | "Programmes you can apply to in the same field" |
| **Academic no-match** | Shown when nothing in the chosen fields is Eligible or Potentially Eligible. Plain explanation of the main reason (e.g., "Most programmes need Mathematics"); cards for related fields with counts; deficiency/entry-test routes; buttons: "Change my fields", "Check my marks". No budget/location suggestions here |
| **Preference no-match** | Shown when the student qualifies but nothing fits preferences. "You meet the requirements for 11 programmes" + one-tap suggestions with counts ("Raise budget to PKR 80,000 → 6 options"); "Edit preferences" button; "Show all 11 anyway" link |

### 3.4 Explore
| Screen | Content |
|---|---|
| Search | Search bar with suggestions; recent searches; filter button |
| Filters sheet | Province, city, sector, field, fee range, hostel (boys/girls), campus type, entry test, accreditation, shift |
| University detail | Header (logo, name, sector, HEC status), tabs: Overview · Campuses · Programmes · Fees · Hostels · Contact; official links; verified date |
| Programme detail | Eligibility rules in plain words, per background; fees; tests; deadlines; seats; accreditation; sources; "Check my eligibility" button |
| Map (later) | Campus pins |

### 3.5 Shortlist
| Screen | Content |
|---|---|
| Shortlist | Saved programmes with status and next deadline; swipe to remove |
| Compare (2–3) | Side-by-side table: status, fee/semester, first-year total, hostel, test, deadline, accreditation, city |
| Deadlines | Timeline of upcoming dates for saved items; reminder toggles |

### 3.6 Chat
| Screen | Content |
|---|---|
| Chat | Message list, streaming replies, source cards, action buttons, 👍/👎, suggested questions, AI label, daily limit counter |
| Chat history | Previous conversations (optional) |

### 3.7 Profile and settings
| Screen | Content |
|---|---|
| Profile overview | Completion %, sections with edit buttons |
| Education records | Edit qualifications, subjects, marks |
| Test scores | |
| Preferences | Same as wizard step 6 |
| Notifications | Deadline reminders, data change alerts |
| Language | English (Urdu later) |
| Appearance | Light / dark / system |
| Privacy & data | Download my data, delete account, privacy policy, consents |
| Help | FAQ, guides, contact support |
| About | Data sources explanation ("Where our information comes from"), disclaimer, version |
| Log out | Confirmation dialog; clears the session and tokens on this device; returns to Sign in *(PDF FR-01)* |

## 4. Main user journeys

### Journey A — New student finds options
Welcome → Sign up → Verify email → Profile wizard (6 steps) → Review → **Results summary** → Eligible list → Result detail → Save → Official admission page.

### Journey B — Student waiting for Inter result
Wizard step 3: chooses "Part-I only" → enters Part-I marks → results show more "Potentially Eligible" with clear notes → later edits profile with final marks → "Update results" banner → results refresh.

### Journey C — "Why am I not eligible?"
Not eligible list → Result detail shows ❌ reason → taps "Ask assistant" → chat explains using saved result → suggests alternatives → student opens alternative.

### Journey D — Parent comparing costs
Explore → filter by city + hostel (girls) + budget → compare 3 programmes → sees first-year total cost with hostel.

### Journey F — No match found (from the Workflow PDF, corrected)
**F1 — Academic no-match:** Pre-Medical student chooses only Engineering → Results → **Academic no-match** screen ("Most engineering programmes need Mathematics") → taps "BS Biotechnology (9 options)" → results for the new field → Save.

**F2 — Preference no-match:** ICS student qualifies for 11 programmes but budget is PKR 40,000 and only Lahore is chosen → **Preference no-match** screen → taps "Add Islamabad → 4 options" → ranked results appear (eligibility is not re-checked, only ranking).

### Journey E — Reporting wrong data
Programme detail → "Report incorrect info" → choose field (fee / rule / deadline / other) → add note or screenshot → submitted → (admin fixes) → student gets "Thanks, we updated it" notification.

## 5. Visual design direction

- Calm, trustworthy palette (e.g., deep green or blue primary), high contrast text.
- Status colours: green (eligible), amber (potentially), red-grey (not currently) — always with icons.
- Typography: a clear sans-serif with good Urdu companion font later (e.g., Noto Sans + Noto Nastaliq Urdu).
- Cards with clear hierarchy: programme name biggest, university second, facts as chips.
- Material 3 components in Flutter for consistency and accessibility.
- Empty states with guidance ("No results in your budget. Try raising it or include more provinces.").

## 6. Before coding UI

1. Low-fidelity wireframes for all screens (Figma or paper).
2. Test the profile wizard with 5–8 real students (Matric, FSc, ICS, A-Level, DAE backgrounds) — watch where they get stuck.
3. High-fidelity designs for core flows.
4. Design system: colours, text styles, spacing, components — mapped to Flutter theme.
