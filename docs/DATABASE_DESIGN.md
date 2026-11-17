# Database Design

Database: **PostgreSQL** (Supabase) with the `pgvector` and `pg_trgm` extensions.

This is a **logical design** (tables, key fields, relationships). Exact column types and migrations come in the implementation phase after approval.

---

## 1. Design ideas

1. **Separate "what exists" from "what is offered this year".**
   A *programme* (e.g., BS Computer Science at COMSATS Lahore campus) exists for many years. Its *offering* for the 2027 admission cycle has its own rules, fees, seats, and deadlines. This lets us keep history and warn when data is old.
2. **Rules are data.** Eligibility rules are rows with a type and parameters, not code.
3. **Every fact has a source.** Rules, fees, hostels, and deadlines link to a `sources` record (URL or uploaded PDF + page) and have a verification status.
4. **Lookup tables instead of fixed lists.** Provinces, boards, qualification types, groups, subjects, programme fields are all tables. New ones are added by admins.
5. **Students' data is separated from catalogue data** and protected by row-level security.
6. **Money is stored as whole rupees (integer)** with a `fee_basis` (per semester, per year, per credit hour, one-time).

Common fields on most tables (not repeated below): `id (uuid)`, `created_at`, `updated_at`, `created_by`, `updated_by`.

Verification fields on catalogue tables (marked **[V]** below): `status` (`draft`, `pending_review`, `verified`, `published`, `archived`), `source_id`, `verified_by`, `verified_at`.

---

## 2. Entity overview

```
REFERENCE DATA
  regions ─< districts ─< cities
  exam_boards
  qualification_levels ─< qualification_types ─< qualification_groups ─< group_subjects >─ subjects
  programme_fields ─< programme_disciplines
  entry_tests
  admission_cycles

CATALOGUE
  universities ─< campuses ─< programmes ─< offerings ─< eligibility_rule_sets ─< eligibility_rules
                     │                         ├─< offering_fees
                     │                         ├─< offering_entry_tests >─ entry_tests
                     │                         ├─< offering_deadlines
                     │                         └─< offering_quotas
                     ├─< hostels ─< hostel_fees
                     └─ (gender_policy, address, geo)
  universities ─< university_accreditations / programmes ─< programme_accreditations
  sources (URL / PDF) ── referenced by most catalogue rows
  merit_formulas (later) ─ offering

STUDENT DATA
  users (auth) ─ student_profiles
               ─< student_qualifications ─< student_qualification_subjects
               ─< student_test_scores
               ─ student_preferences (+ preference_regions, preference_cities, preference_fields, ...)
               ─< shortlists
               ─< recommendation_runs ─< recommendation_results
               ─< consents
               ─< device_tokens

CHAT & KNOWLEDGE
  kb_documents ─< kb_chunks (embedding vector)
  chat_sessions ─< chat_messages ─< chat_message_sources
                                 ─ chat_feedback

ADMIN & QUALITY
  admin_users / roles
  data_reports (from students)
  audit_log
  data_versions (publish snapshots)
```

---

## 3. Reference tables

### `regions`
Provinces and territories: Punjab, Sindh, Khyber Pakhtunkhwa, Balochistan, Gilgit-Baltistan, Islamabad Capital Territory, Azad Jammu & Kashmir.
- `code` (e.g., `PB`, `SD`, `KP`, `BA`, `GB`, `ICT`, `AJK`), `name`, `name_ur`, `type` (`province`, `territory`), `is_active`

### `districts`
- `region_id`, `name`, `name_ur` — needed for domicile and quota rules.

### `cities`
- `district_id`, `name`, `name_ur`, `latitude`, `longitude`

### `exam_boards`
- `name` (e.g., BISE Lahore, Federal Board (FBISE), Aga Khan University Examination Board, Cambridge International, Pearson Edexcel, Punjab Board of Technical Education, Sindh Board of Technical Education), `short_name`, `region_id` (nullable), `board_kind` (`bise`, `federal`, `private`, `foreign`, `technical`)

### `qualification_levels`
- `code`: `SSC` (secondary / Matric level), `HSSC` (higher secondary / Intermediate level), `DIPLOMA` (e.g., DAE), `BACHELOR_2Y` (for lateral entry — later)
- `name`, `sort_order`

### `qualification_types`
- `level_id`, `code`, `name`. Examples: `MATRIC`, `O_LEVEL`, `INTERMEDIATE`, `A_LEVEL`, `DAE`, `OTHER`.

### `qualification_groups`
The stream within a type.
- `type_id`, `code`, `name`. Examples:
  - Matric: `SCIENCE_BIO`, `SCIENCE_COMP`, `ARTS`, `TECHNICAL`
  - Intermediate: `PRE_ENGINEERING`, `PRE_MEDICAL`, `ICS`, `ICOM`, `FA`, `GENERAL_SCIENCE`, `FA_IT`
  - DAE: `ELECTRICAL`, `MECHANICAL`, `CIVIL`, `CIT`, `ELECTRONICS`, ...
  - A-Level: `A_LEVEL` (subjects chosen freely)
- `allows_custom_subjects` (bool) — true for A-Levels and "Other".

### `subjects`
- `code`, `name`, `name_ur`. Examples: `MATH`, `PHY`, `CHEM`, `BIO`, `CS`, `STAT`, `ECON`, `ACCT`, `ENG`, `URDU`...

### `group_subjects`
Default subject combinations per group.
- `group_id`, `subject_id`, `is_compulsory` (bool), `choice_set` (nullable text; subjects with the same choice set are "pick one"). Example — ICS: MATH (compulsory), CS (compulsory), PHY (choice_set=`ICS_3`), STAT (choice_set=`ICS_3`), ECON (choice_set=`ICS_3`).

### `programme_fields`
Broad fields: Computing, Engineering, Medical & Dental, Allied Health, Business & Management, Social Sciences, Natural Sciences, Arts & Humanities, Law, Agriculture, Architecture & Design, Education, Engineering Technology...

### `programme_disciplines`
- `field_id`, `name` (e.g., Computer Science, Software Engineering, Artificial Intelligence, Data Science, Electrical Engineering, MBBS, BDS, Pharm-D, DPT, BBA...), `degree_level` (`bachelor`), `typical_duration_years`.

### `entry_tests`
- `code` (`ECAT`, `MDCAT`, `NAT_IE`, `NAT_ICS`, `NET`, `SAT`, `UNI_SPECIFIC`...), `name`, `conducted_by`, `website`, `score_total`, `validity_note`.

### `admission_cycles`
- `year` (e.g., 2027), `label` (`Fall 2027`), `is_current` (bool), `starts_on`, `ends_on`.

### `accreditation_bodies`
- `code` (`HEC`, `PEC`, `PMDC`, `NCEAC`, `NBEAC`, `PCP`, `PNC`, `NAEAC`...), `name`, `website`.

---

## 4. Catalogue tables

### `universities` **[V]**
| Field | Notes |
|---|---|
| `name`, `short_name`, `aliases` (text[]) | Aliases help search ("UET", "NUST") |
| `sector` | `public`, `private`, `semi_government` (incl. armed-forces-run / public-private) |
| `hec_recognised` (bool), `hec_category` (nullable) | From HEC list |
| `charter_region_id` | Where chartered |
| `gender_policy` | `coeducation`, `women_only`, `men_only` (university-wide default) |
| `website_url`, `admissions_url` | Official only |
| `logo_path` | Storage path |
| `description` | Short, neutral text |

### `campuses` **[V]**
| Field | Notes |
|---|---|
| `university_id` | |
| `name` (e.g., "Lahore Campus"), `is_main_campus` | |
| `city_id`, `address`, `latitude`, `longitude` | |
| `gender_policy` | Overrides university default (some campuses are women-only) |
| `admissions_url` | If campus-specific |
| `has_transport` | Later |

### `programmes` **[V]**
A degree as offered at a campus (stable across years).
| Field | Notes |
|---|---|
| `campus_id`, `discipline_id` | |
| `title` (as written by the university, e.g., "BS (Artificial Intelligence)") | |
| `degree_type` (`BS`, `BE`, `BSc_Eng`, `BSc_Eng_Tech`, `MBBS`, `BDS`, `Pharm_D`, `DPT`, `BBA`, `LLB`...) | |
| `duration_years`, `total_credit_hours` | |
| `shift` (`morning`, `evening`, `weekend`) | Separate rows if rules/fees differ |
| `programme_url` | |

### `programme_accreditations` **[V]**
- `programme_id`, `body_id`, `status` (`accredited`, `provisional`, `not_accredited`, `unknown`), `valid_until`, `source_id`.

### `offerings` **[V]**
One programme in one admission cycle.
| Field | Notes |
|---|---|
| `programme_id`, `cycle_id` | Unique together |
| `is_offered` (bool) | Some programmes are not offered every year |
| `seats_total` (nullable) | |
| `notes` | Free text shown to students (verified) |
| `data_carried_from_cycle_id` | If copied from last year and not yet re-verified |

### `eligibility_rule_sets` **[V]**
Groups rules for an offering. An offering can have **more than one rule set** for different backgrounds (e.g., set A for FSc Pre-Engineering, set B for ICS, set C for DAE). A student is eligible if they pass **any one** set.
| Field | Notes |
|---|---|
| `offering_id` | |
| `name` (e.g., "For ICS students") | |
| `logic` | `all` (every rule must pass) — default |
| `priority` | Display order |
| `rule_schema_version` | For future changes in rule format |

### `eligibility_rules` **[V]**
| Field | Notes |
|---|---|
| `rule_set_id` | |
| `rule_type` | See list below |
| `params` (JSONB) | Rule details, validated by the backend per `rule_type` |
| `is_hard` (bool) | Hard = failing makes "Not eligible". Soft = failing makes "Potentially eligible" |
| `student_message_pass` / `student_message_fail` | Optional custom text; otherwise templates are used |
| `source_id` | Page/section in the prospectus |

**Rule types (initial set):**

| `rule_type` | Example `params` |
|---|---|
| `accepted_qualification` | `{"level": "HSSC", "types": ["INTERMEDIATE","A_LEVEL"], "groups": ["PRE_ENGINEERING","ICS"]}` |
| `required_subjects` | `{"level": "HSSC", "all_of": ["MATH"], "one_of": [["PHY","CS","STAT"]]}` |
| `min_percentage` | `{"level": "HSSC", "min": 50, "basis": "total_marks"}` |
| `min_subject_marks` | `{"level": "HSSC", "subject": "MATH", "min_percentage": 50}` |
| `min_percentage_combined` | `{"levels": ["SSC","HSSC"], "min": 60}` |
| `entry_test_required` | `{"tests": ["ECAT","UNI_SPECIFIC"], "any_of": true, "min_score_percentage": 33}` |
| `gender` | `{"allowed": ["female"]}` |
| `domicile` | `{"regions": ["BA"], "seat_type": "quota"}` (used with quotas) |
| `max_age` | `{"years": 24, "on_date": "2027-08-31"}` |
| `passing_year_window` | `{"level": "HSSC", "min_year": 2025}` |
| `result_status` | `{"level": "HSSC", "accept_part1": true, "min_part1_percentage": 60}` |
| `deficiency_allowed` | `{"for_groups": ["PRE_MEDICAL"], "missing_subject": "MATH", "course": "Deficiency Mathematics (6 credit hours) in first year"}` |
| `ibcc_equivalence_required` | `{"for_types": ["A_LEVEL","O_LEVEL"]}` |
| `improved_result_policy` | `{"accepted": false}` |
| `manual_note` | `{"text": "Interview required"}` — always gives "Potentially eligible" with a note |

New rule types can be added later by adding a validator + evaluator in the backend; the database does not change.

### `offering_quotas` **[V]** (should-have)
- `offering_id`, `quota_type` (`open_merit`, `regional`, `disabled`, `sports`, `hafiz`, `minority`, `employees_children`, `overseas`, `fata_balochistan`...), `seats`, `extra_rule_set_id` (nullable).

### `offering_fees` **[V]**
One row per fee item.
| Field | Notes |
|---|---|
| `offering_id` | |
| `component` | `admission` (one-time), `tuition`, `registration`, `exam`, `library`, `lab`, `security_refundable`, `other` |
| `amount_pkr` (integer) | |
| `basis` | `one_time`, `per_semester`, `per_year`, `per_credit_hour` |
| `applies_to_semester` | e.g., `first_only`, `all` |
| `is_estimated` (bool) | If calculated (e.g., credit-hour × typical credits) |
| `source_id` | |

The backend calculates **comparable totals** from these rows: *per-semester tuition*, *first-semester total*, *first-year total*, *whole-degree estimate*.

### `offering_entry_tests` **[V]**
- `offering_id`, `entry_test_id`, `is_mandatory`, `weightage_percent` (for merit, later), `min_score`, `test_date`, `registration_deadline`.

### `offering_deadlines` **[V]**
- `offering_id`, `event` (`applications_open`, `applications_close`, `test_date`, `merit_list`, `classes_start`), `date`, `is_tentative`.

### `hostels` **[V]**
| Field | Notes |
|---|---|
| `campus_id` | |
| `for_gender` | `male`, `female` |
| `location` | `on_campus`, `off_campus_university_managed`, `affiliated_private` |
| `availability` | `available`, `limited`, `not_available`, `unknown` |
| `capacity` (nullable), `notes` | |

### `hostel_fees` **[V]**
- `hostel_id`, `cycle_id`, `component` (`room`, `mess`, `security`, `other`), `amount_pkr`, `basis`, `source_id`.

### `merit_formulas` (later)
- `offering_id`, `components` JSONB, e.g., `[{"part":"SSC","weight":10},{"part":"HSSC","weight":40},{"part":"TEST","test":"ECAT","weight":50}]`.

### `sources`
| Field | Notes |
|---|---|
| `kind` | `web_page`, `pdf_prospectus`, `official_notice`, `email_from_university`, `phone_call_note` |
| `url`, `storage_path` (for uploaded PDF), `page_numbers` | |
| `title`, `publisher` (university / HEC / PEC / PM&DC...), `cycle_id` | |
| `retrieved_at`, `content_hash` | Hash lets the link-checker detect when a page changed |
| `is_official` (bool) | Only official sources are allowed for verified data |

### `data_versions`
- `version_no`, `published_at`, `published_by`, `notes`. Every "publish" creates a version. Recommendation runs store which version they used.

---

## 5. Student tables (protected by row-level security)

### `student_profiles`
| Field | Notes |
|---|---|
| `user_id` (= auth user id) | |
| `full_name`, `phone`, `gender`, `date_of_birth` | |
| `current_city_id`, `domicile_district_id` | |
| `special_categories` (text[]) | Optional, opt-in |
| `profile_completed_at` | |
| `language` | `en`, `ur` |

### `student_qualifications`
| Field | Notes |
|---|---|
| `user_id`, `level_id`, `type_id`, `group_id`, `board_id` | |
| `passing_year`, `result_status` (`final`, `part1_only`, `awaited`) | |
| `obtained_marks`, `total_marks`, `percentage` (stored, calculated) | |
| `part1_obtained`, `part1_total` | For students waiting for final results |
| `ibcc_equivalence_percentage`, `ibcc_is_official` (bool) | For O/A-Levels |
| `is_improved_result` | |
| `dae_discipline` | For DAE (or use group) |

### `student_qualification_subjects`
- `qualification_id`, `subject_id`, `obtained_marks` (nullable), `total_marks` (nullable), `grade` (for A-Levels).

### `student_test_scores`
- `user_id`, `entry_test_id`, `year`, `score`, `total`, `is_expected` (student entered expected score — used only for "what if").

### `student_preferences`
| Field | Notes |
|---|---|
| `user_id` | |
| `max_fee_per_semester_pkr` (nullable) | |
| `budget_includes` | `tuition_only`, `university_charges`, `with_hostel` |
| `sectors` (text[]) | |
| `hostel_need` | `none`, `needed`, `on_campus_only` |
| `gender_campus_pref` | `any`, `coeducation`, `single_gender` |
| `shifts` (text[]) | |
| `require_accreditation` (bool) | |
| `max_distance_km` (nullable) | |
| `willing_tests` (text[]) | |

Linked tables: `preference_regions (user_id, region_id)`, `preference_cities (user_id, city_id)`, `preference_fields (user_id, field_id)`, `preference_disciplines (user_id, discipline_id)`.

### `shortlists`
- `user_id`, `offering_id`, `note`, `created_at`.

### `recommendation_runs`
- `user_id`, `data_version_id`, `engine_version`, `profile_snapshot` (JSONB, copy of inputs), `preferences_snapshot` (JSONB), `created_at`, `is_latest`.

### `recommendation_results`
| Field | Notes |
|---|---|
| `run_id`, `offering_id` | |
| `category` | `eligible`, `potentially_eligible`, `not_eligible` |
| `matched_rule_set_id` | Which background path matched |
| `rule_outcomes` (JSONB) | List of `{rule_id, type, outcome: pass/fail/unknown, reason_code, message}` |
| `next_steps` (JSONB) | e.g., "Register for ECAT before 15 June" |
| `within_preferences` (bool), `preference_misses` (text[]) | e.g., `["over_budget"]` |
| `match_score` (0–100) | For sorting only |
| `data_is_stale` (bool) | |

### `consents`
- `user_id`, `policy_type` (`privacy`, `terms`, `ai_assistant`), `policy_version`, `accepted_at`.

### `device_tokens`
- `user_id`, `platform`, `fcm_token`, `last_seen_at`.

---

## 6. Chatbot and knowledge tables

### `kb_documents`
| Field | Notes |
|---|---|
| `kb` | `app_help`, `admissions`, `guides` |
| `title`, `source_id` (nullable), `entity_type` + `entity_id` (e.g., offering) | |
| `cycle_id` | For admissions content |
| `status` | Only `published` documents are searchable |
| `content_markdown`, `content_hash` | |

### `kb_chunks`
- `document_id`, `chunk_index`, `content`, `embedding vector(N)` (N depends on chosen model), `metadata` JSONB (university_id, region, discipline, cycle, verified_at), `tsv` (full-text search column).
- Indexes: HNSW on `embedding`, GIN on `tsv`, B-tree on metadata keys used for filters.

### `chat_sessions`
- `user_id`, `started_at`, `title`.

### `chat_messages`
- `session_id`, `role` (`user`, `assistant`), `content`, `intent` (`app_help`, `admissions`, `my_results`, `off_topic`), `model`, `input_tokens`, `output_tokens`, `latency_ms`.

### `chat_message_sources`
- `message_id`, `chunk_id`, `source_id`, `score`.

### `chat_feedback`
- `message_id`, `user_id`, `rating` (`up`, `down`), `reason` (`wrong`, `outdated`, `not_helpful`, `other`), `comment`, `review_status`.

---

## 7. Admin and quality tables

### `admin_roles` / `user_roles`
- Roles: `super_admin`, `data_editor`, `data_verifier`, `support`. A user can have several roles. Editors cannot verify their own changes.

### `data_reports`
Student reports of wrong information.
- `user_id`, `entity_type`, `entity_id`, `field`, `message`, `screenshot_path`, `status` (`new`, `in_review`, `fixed`, `rejected`), `handled_by`.

### `audit_log`
- `actor_id`, `action` (`create`, `update`, `delete`, `verify`, `publish`, `login`), `entity_type`, `entity_id`, `before` JSONB, `after` JSONB, `ip`, `at`.

---

## 8. Indexes and search

- `pg_trgm` GIN indexes on `universities.name`, `aliases`, `programmes.title` for fuzzy search ("comsat", "uet lhr").
- Composite indexes on `offerings (cycle_id, programme_id)`, `campuses (city_id)`, `offering_fees (offering_id, component)`.
- A **materialised view** `offering_search_view` that flattens university + campus + programme + fees + hostel flags for fast filtering in the app. Refreshed on every publish.

## 9. Row-level security (summary)

| Table group | Students | Admin roles |
|---|---|---|
| Reference + catalogue | Read **published** rows only | Editors write drafts; verifiers verify; super admin all |
| Student tables | Read/write own rows (`user_id = auth.uid()`) | Support: read limited fields; super admin: delete on request |
| Chat tables | Own sessions only | Support/super admin: read anonymised for review |
| Audit log | No access | Super admin read only; nobody can edit |

## 10. Data lifecycle

- **New admission cycle:** a script copies last year's offerings, rules, fees, deadlines into the new cycle with status `draft` and `data_carried_from_cycle_id` set. Students see the old verified data with a "previous cycle" warning until the new data is verified.
- **Archive, don't delete:** old cycles stay for history and past explanations.
- **Student deletion:** hard-delete personal rows; keep anonymised counts only.
