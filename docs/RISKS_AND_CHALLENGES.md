# Risks and Challenges

Each risk has: **Impact** (High / Medium / Low), **Likelihood** (High / Medium / Low), and how we plan to handle it.

---

## 1. Data risks (biggest area)

| # | Risk | Impact | Likelihood | Plan |
|---|---|---|---|---|
| D1 | **No central official source.** Each university publishes rules in its own format (websites, PDFs, newspaper ads, social media). | High | High | Start with a pilot set; trained data team; two-person verification; only official sources accepted; store page references. |
| D2 | **Data changes every year** (fees, rules, deadlines) and sometimes mid-season. | High | High | Offerings per admission cycle; "copy from last year" as draft; stale warnings; weekly link/page-change checker; re-verification calendar before each season. |
| D3 | **Information is incomplete or unclear** (e.g., "other relevant qualifications", "as per HEC policy"). | High | High | Rule outcome `UNKNOWN` → "Potentially Eligible" with a note; never guess; record "unclear" items for follow-up with the university. |
| D4 | **Wrong data entered by mistake.** | High | Medium | Four-eyes verification; validation rules (e.g., fee ranges); student "report error" button; audit log; golden tests. |
| D5 | **Campus-level and shift-level differences** (same programme, different rules/fees). | Medium | High | Data model is per campus + shift + cycle. |
| D6 | **Hostel information is rarely published clearly.** | Medium | High | Allow `unknown`; show "Contact university"; collect over time. |
| D7 | **Data entry workload is underestimated.** Rough guide: 1–3 hours per university per cycle for the pilot programme families, plus verification. | High | High | Budget data team time from day 1; start with fewer universities; later add AI-assisted extraction (human-verified). |
| D8 | **Copyright/terms of university websites** when copying content. | Low | Low | Store facts (fees, rules) and links, not copied page text; link to the original; respect robots/terms for any automated checking. |

## 2. Accuracy and trust risks

| # | Risk | Impact | Likelihood | Plan |
|---|---|---|---|---|
| A1 | **Students read "Eligible" as "I will get admission".** | High | High | Clear wording everywhere; no admission chance shown; disclaimer on results and chat; counsellor-reviewed text. |
| A2 | **A student misses an opportunity because we said "Not eligible" wrongly.** | High | Medium | Use "Not *currently* eligible"; always show the exact reason and source; uncertain cases go to "Potentially"; students can report. |
| A3 | **Chatbot makes up rules or fees.** | High | Medium | Verified-only retrieval, mandatory citations, number checking, SQL facts for numbers, evaluation set, review of 👎. |
| A4 | **Students enter wrong marks.** | Medium | Medium | Validation, calculated percentage, review screen; results show "based on your entered marks". |
| A5 | **A-Level IBCC equivalence estimates are wrong.** | Medium | Medium | Mark estimated values; results become "Potentially"; guide on getting the official certificate. |
| A6 | **Legal complaint from a university about wrong information.** | Medium | Low | Sources and dates shown; quick correction process; terms of use; disclaimer; contact page for universities. |

## 3. Technical risks

| # | Risk | Impact | Likelihood | Plan |
|---|---|---|---|---|
| T1 | **Rule format cannot express some real rules.** | High | Medium | Test the format against 10+ real prospectuses in Phase 1; `manual_note` fallback; versioned rule schema; add new rule types in backend only. |
| T2 | **Admission-season traffic spikes.** | Medium | High | Auto-scaling API; cached catalogue; CDN for images; load testing before launch. |
| T3 | **AI costs grow faster than expected.** | Medium | Medium | Daily limits, prompt caching, answer cache, model choice by measured quality/cost, spend alerts. |
| T4 | **AI provider outage or API changes.** | Medium | Low | App works without chat; provider wrapped in one module; monitor; fallback message. |
| T5 | **Vendor lock-in (Supabase).** | Low | Low | Supabase is standard PostgreSQL and open source; business logic lives in FastAPI; can move to any Postgres host. |
| T6 | **Weak internet / old phones.** | Medium | High | Light app, caching, pagination, testing on low-end devices. |
| T7 | **Small team; key person leaves.** | High | Medium | Documentation, code reviews, tests, simple stack choices. |

## 4. Security and privacy risks

| # | Risk | Impact | Likelihood | Plan |
|---|---|---|---|---|
| S1 | **Leak of student personal data** (many users are minors). | High | Low | RLS, least privilege, encryption, no personal data in logs/analytics/AI prompts, security testing. |
| S2 | **Admin account takeover** → false data published. | High | Low | 2FA, four-eyes publishing, audit log, alerts, quick rollback via data versions. |
| S3 | **Prompt injection** through documents or questions. | Medium | Medium | Chatbot is read-only; documents treated as data; only admin-approved content indexed. |
| S4 | **Legal requirements unclear** (Pakistan data protection law status, minors' data). | Medium | Medium | Legal review before launch; follow good international practice (consent, access, deletion, minimisation) anyway. |
| S5 | **Fake accounts / abuse of chatbot.** | Low | Medium | Email verification, rate limits, daily chat limits, CAPTCHA on sign-up if abuse appears. |

## 5. Product and business risks

| # | Risk | Impact | Likelihood | Plan |
|---|---|---|---|---|
| P1 | **Low adoption** — students keep using social media groups. | High | Medium | Partner with colleges/academies; useful free features; shareable results; launch before admission season. |
| P2 | **No sustainable funding for data upkeep.** | High | Medium | Decide business model early (see open questions); keep costs low. |
| P3 | **Scope creep** (postgraduate, foreign universities, payments...). | Medium | High | Strict MVP scope; "later" list; owner approval for changes. |
| P4 | **Launch misses the admission season** (most applications June–September). | High | Medium | Plan the beta for the spring before the season; pilot scope keeps the timeline realistic. |
| P5 | **Perceived bias** (e.g., if paid listings are added later). | Medium | Low | Never let payments affect eligibility or ranking; label any sponsored content clearly. |

## 6. Top 5 risks to watch

1. D1/D7 — Data collection effort and quality.
2. A1/A2 — Students misunderstanding eligibility.
3. A3 — Chatbot inventing facts.
4. P4 — Missing the admission season.
5. T1 — Rule format not covering real-world rules.
