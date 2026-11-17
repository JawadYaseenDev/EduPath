# Open Questions for the Project Owner

These decisions change the plan. Please answer them before implementation starts. Suggested defaults are given in brackets.

## Baseline document
0. ~~Is the Workflow PDF a fixed specification?~~ **Answered: yes, fixed.** AI assistant and notifications moved to version 1.1.
0a. **Waiting for supervisor:** may we add the Potentially Eligible group and the two separate no-match paths? See [CHANGE_REQUEST_FOR_SUPERVISOR.md](CHANGE_REQUEST_FOR_SUPERVISOR.md). If not approved, the engine runs in strict PDF mode.

## Team, time, and money
1. **Who is building this?** How many developers, and which skills (Flutter only? Python? React?). [Assumed: 2 developers + part-time help]
2. **Is this a commercial product, a startup, or an academic / final-year project?** This changes scope, timeline, and legal work.
3. **Target launch date?** Should we aim to launch before a specific admission season (e.g., Fall 2027)?
4. **Monthly budget** for hosting + AI? [Assumed: about USD 100/month for the MVP]
5. **Business model** (free, ads, premium features, partnerships with colleges/universities)? Matters for long-term data upkeep.

## Scope
6. **Approve the pilot scope?** About 40–60 universities; Computing, Engineering, Business, Medical/Allied; data first for Punjab + Islamabad + one more region. Or do you want all regions in v1?
7. **Should AJK be included** as a region? [Recommended: yes]
8. **Medical admissions (MBBS/BDS)** are mostly decided by MDCAT and provincial admission authorities, not each college. Include them in v1 or later?
9. **Android only for MVP**, iOS later? [Recommended: yes]
10. **Urdu** in v1 or after? [Recommended: after MVP, but design for it now]
11. **Guest browsing** without an account? [Recommended: yes]

## Data
12. **Who will collect and verify data?** Do you have people for this, and how many hours per week?
13. Do you have **contacts in universities, HEC, or colleges** who could help confirm data?
14. Is there an **education counsellor** who can review rules, explanations, and test cases?

## Technology
15. **Admin panel:** React (Next.js) or Flutter Web? [Recommended: React if someone knows it; otherwise Flutter Web]
16. **Phone OTP sign-up:** SMS costs money per message. Include in v1? [Recommended: email + Google first]
17. **AI model:** We will compare `claude-opus-5-5`, `claude-sonnet-5-5`, and `claude-haiku-5-5` on our evaluation set and show you quality vs cost. Are you happy to make the final choice after that test?
18. **Data hosting location:** any requirement that data stays in Pakistan or a specific region? (Affects provider choice.)

## Legal
19. Do you have access to a **lawyer** for privacy policy, terms, and Pakistan data protection review?
20. Minimum user **age**? Under-18 users are common; should we add a parent/guardian notice?
