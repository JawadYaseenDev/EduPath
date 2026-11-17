# Change Request: Student Recommendation Workflow

**Document:** Student_Recommendation_Workflow_and_Requirements-1.pdf (FR-01 to FR-06)
**Requested by:** Project team
**Date:** 18 November 2026
**Status:** Waiting for approval

---

## Summary

We will deliver **all** requirements FR-01 to FR-06 as written. We ask for approval of **three small changes to the workflow diagram**. None of them relax academic eligibility, and none add new scope to FR-01 to FR-06. They make the results more accurate and the "no match" step actually useful.

If any change is not approved, the system will follow the original diagram exactly. The design already supports both options, so there is no delay either way.

---

## Change 1 — Add a "Potentially Eligible" group

**Original diagram:** each option is either eligible (ranked) or not.

**Problem:** in Pakistan many students apply **before** their final Intermediate result (on Part-I marks), A-Level students may not yet have their IBCC equivalence certificate, and some programmes require an interview. The system cannot honestly say "eligible" or "not eligible" for these students.

**Proposed:** show a separate group, **Potentially Eligible**, for options where the student fails **no** known requirement but at least one cannot be confirmed yet. Each one says exactly what must be confirmed (e.g., "Your final result must also be 60% or more").

**Why it does not relax eligibility:** if the student fails any known requirement, the option is still "not eligible". Potentially Eligible options are ranked in their own group and never mixed with Eligible ones.

**Example:** an ICS student with 64% in Part-I applying for a programme that needs 60%. Original: must be shown as eligible (risky) or not eligible (wrong). Proposed: Potentially Eligible — "Based on Part-I you are above 60%; your final result must also meet it."

☐ Approved ☐ Not approved

---

## Change 2 — Two separate "no match" paths

**Original diagram:** one box, "Matching options available? → No → Show no-match explanation, suggest preference changes".

**Problem:** there are two different reasons for "no match":
- **Academic:** e.g., a Pre-Medical student who chose only Engineering. Changing budget or location can **never** help, so suggesting it sends the student into a loop with no exit.
- **Preferences:** the student qualifies, but nothing fits the budget or location.

**Proposed:**
- *Academic no-match:* explain the main failed requirement (e.g., "Most engineering programmes need Mathematics") and suggest related fields, deficiency-course routes, or entry-test routes.
- *Preference no-match:* show which change unlocks how many options (e.g., "Raise budget to PKR 80,000 → 6 options").

This still meets FR-04: "Show a no-match message and allow preference changes when necessary."

☐ Approved ☐ Not approved

---

## Change 3 — Revise loop returns to the correct step

**Original diagram:** "Student revises preferences and requests a new search" returns to "Apply budget and location preferences".

**Problem:** if the student corrects their **marks or subjects**, eligibility must be checked again, but the loop skips that step.

**Proposed:**
- Changes to academic data → return to "Check academic eligibility".
- Changes to preferences only → return to "Apply budget and location preferences" (as in the original).

☐ Approved ☐ Not approved

---

## Corrected diagram

The full corrected workflow diagram is in [RECOMMENDATION_ENGINE.md § 0](RECOMMENDATION_ENGINE.md#0-end-to-end-workflow-aligned-with-the-workflow-pdf). It keeps the three stages of the original: **01 Student Input → 02 Matching & Ranking → 03 Results & Decision**.

## What does not change

- All FR-01 to FR-06 bullet points.
- "Rank only eligible offerings. Do not relax academic eligibility."
- "Recommendations support decisions; they do not guarantee admission."
- Rules-based, transparent ranking using curated institutional data.

## Signatures

Supervisor: ____________________  Date: ____________

Project lead: __________________  Date: ____________
