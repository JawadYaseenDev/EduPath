"""Seed data.

1. Reference data (regions, cities, boards, qualification types, groups, subjects,
   fields, entry tests): general facts about Pakistan's education system. Admins can
   edit all of it later.

2. DEMO catalogue: FICTIONAL universities for development and testing only.
   Every demo university is named "Demo ...", has is_demo=True, and uses a "demo"
   source. The app labels them "Sample data - not a real university".
   Real university data must only be entered by admins from official sources.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models as m

REGIONS = [
    ("PB", "Punjab", "province"),
    ("SD", "Sindh", "province"),
    ("KP", "Khyber Pakhtunkhwa", "province"),
    ("BA", "Balochistan", "province"),
    ("ICT", "Islamabad Capital Territory", "territory"),
    ("GB", "Gilgit-Baltistan", "territory"),
    ("AJK", "Azad Jammu & Kashmir", "territory"),
]

CITIES = [
    ("PB", "Lahore", 31.5204, 74.3587), ("PB", "Rawalpindi", 33.5651, 73.0169),
    ("PB", "Faisalabad", 31.4504, 73.1350), ("PB", "Multan", 30.1575, 71.5249),
    ("PB", "Gujranwala", 32.1877, 74.1945), ("PB", "Bahawalpur", 29.3956, 71.6836),
    ("PB", "Sialkot", 32.4945, 74.5229), ("PB", "Sargodha", 32.0836, 72.6711),
    ("PB", "Taxila", 33.7463, 72.8397),
    ("SD", "Karachi", 24.8607, 67.0011), ("SD", "Hyderabad", 25.3960, 68.3578),
    ("SD", "Jamshoro", 25.4304, 68.2809), ("SD", "Sukkur", 27.7052, 68.8574),
    ("SD", "Larkana", 27.5570, 68.2264),
    ("KP", "Peshawar", 34.0151, 71.5249), ("KP", "Abbottabad", 34.1688, 73.2215),
    ("KP", "Mardan", 34.1986, 72.0404), ("KP", "Swat", 34.7717, 72.3602),
    ("KP", "Dera Ismail Khan", 31.8314, 70.9019),
    ("BA", "Quetta", 30.1798, 66.9750), ("BA", "Gwadar", 25.1264, 62.3225),
    ("BA", "Turbat", 26.0031, 63.0544),
    ("ICT", "Islamabad", 33.6844, 73.0479),
    ("GB", "Gilgit", 35.9208, 74.3144), ("GB", "Skardu", 35.2971, 75.6333),
    ("AJK", "Muzaffarabad", 34.3700, 73.4711), ("AJK", "Mirpur", 33.1484, 73.7518),
]

BOARDS = [
    # (name, short, kind, region)
    ("Board of Intermediate and Secondary Education Lahore", "BISE Lahore", "bise", "PB"),
    ("Board of Intermediate and Secondary Education Rawalpindi", "BISE Rawalpindi", "bise", "PB"),
    ("Board of Intermediate and Secondary Education Gujranwala", "BISE Gujranwala", "bise", "PB"),
    ("Board of Intermediate and Secondary Education Faisalabad", "BISE Faisalabad", "bise", "PB"),
    ("Board of Intermediate and Secondary Education Multan", "BISE Multan", "bise", "PB"),
    ("Board of Intermediate and Secondary Education Sargodha", "BISE Sargodha", "bise", "PB"),
    ("Board of Intermediate and Secondary Education Bahawalpur", "BISE Bahawalpur", "bise", "PB"),
    ("Board of Intermediate and Secondary Education Sahiwal", "BISE Sahiwal", "bise", "PB"),
    ("Board of Intermediate and Secondary Education D.G. Khan", "BISE DG Khan", "bise", "PB"),
    ("Federal Board of Intermediate and Secondary Education", "FBISE", "federal", None),
    ("Board of Intermediate Education Karachi", "BIEK", "bise", "SD"),
    ("Board of Secondary Education Karachi", "BSEK", "bise", "SD"),
    ("Board of Intermediate and Secondary Education Hyderabad", "BISE Hyderabad", "bise", "SD"),
    ("Board of Intermediate and Secondary Education Sukkur", "BISE Sukkur", "bise", "SD"),
    ("Board of Intermediate and Secondary Education Larkana", "BISE Larkana", "bise", "SD"),
    ("Board of Intermediate and Secondary Education Mirpurkhas", "BISE Mirpurkhas", "bise", "SD"),
    ("Board of Intermediate and Secondary Education Peshawar", "BISE Peshawar", "bise", "KP"),
    ("Board of Intermediate and Secondary Education Mardan", "BISE Mardan", "bise", "KP"),
    ("Board of Intermediate and Secondary Education Abbottabad", "BISE Abbottabad", "bise", "KP"),
    ("Board of Intermediate and Secondary Education Swat", "BISE Swat", "bise", "KP"),
    ("Board of Intermediate and Secondary Education Malakand", "BISE Malakand", "bise", "KP"),
    ("Board of Intermediate and Secondary Education Kohat", "BISE Kohat", "bise", "KP"),
    ("Board of Intermediate and Secondary Education Bannu", "BISE Bannu", "bise", "KP"),
    ("Board of Intermediate and Secondary Education D.I. Khan", "BISE DI Khan", "bise", "KP"),
    ("Balochistan Board of Intermediate and Secondary Education Quetta", "BBISE Quetta", "bise", "BA"),
    ("AJK Board of Intermediate and Secondary Education Mirpur", "AJK BISE", "bise", "AJK"),
    ("Aga Khan University Examination Board", "AKU-EB", "private", None),
    ("Cambridge International Education", "Cambridge", "foreign", None),
    ("Pearson Edexcel", "Edexcel", "foreign", None),
    ("Punjab Board of Technical Education", "PBTE", "technical", "PB"),
    ("Sindh Board of Technical Education", "SBTE", "technical", "SD"),
    ("Khyber Pakhtunkhwa Board of Technical Education", "KPBTE", "technical", "KP"),
    ("Other board", "Other", "bise", None),
]

QUAL_TYPES = [
    ("MATRIC", "SSC", "Matric (SSC)", False),
    ("O_LEVEL", "SSC", "O-Levels", True),
    ("OTHER_SSC", "SSC", "Other secondary qualification", False),
    ("INTERMEDIATE", "HSSC", "Intermediate (HSSC)", False),
    ("A_LEVEL", "HSSC", "A-Levels", True),
    ("OTHER_HSSC", "HSSC", "Other higher secondary qualification", False),
    ("DAE", "DIPLOMA", "DAE (Diploma of Associate Engineering)", False),
]

SUBJECTS = [
    ("MATH", "Mathematics"), ("PHY", "Physics"), ("CHEM", "Chemistry"), ("BIO", "Biology"),
    ("CS", "Computer Science"), ("STAT", "Statistics"), ("ECON", "Economics"),
    ("ACCT", "Principles of Accounting"), ("COMM", "Principles of Commerce"),
    ("BMATH", "Business Mathematics & Statistics"), ("ENG", "English"), ("URDU", "Urdu"),
    ("ISL", "Islamiat"), ("PST", "Pakistan Studies"), ("GSCI", "General Science"),
    ("CIVICS", "Civics"), ("PSY", "Psychology"), ("EDU", "Education"),
    ("SOC", "Sociology"), ("GEO", "Geography"), ("HIST", "History"),
    ("FURDU", "Urdu (Elective)"), ("FENG", "English (Elective)"),
]

# (code, type, name, custom_subjects, [(subject, compulsory, choice_set)])
GROUPS = [
    ("MATRIC_SCIENCE_BIO", "MATRIC", "Science (Biology)", False,
     [("MATH", True, None), ("PHY", True, None), ("CHEM", True, None), ("BIO", True, None),
      ("ENG", True, None)]),
    ("MATRIC_SCIENCE_COMP", "MATRIC", "Science (Computer Science)", False,
     [("MATH", True, None), ("PHY", True, None), ("CHEM", True, None), ("CS", True, None),
      ("ENG", True, None)]),
    ("MATRIC_ARTS", "MATRIC", "Arts / Humanities", True,
     [("MATH", False, None), ("GSCI", False, None), ("ENG", True, None)]),
    ("MATRIC_TECH", "MATRIC", "Technical", True, [("MATH", False, None), ("ENG", True, None)]),
    ("O_LEVEL", "O_LEVEL", "O-Levels", True, []),
    ("OTHER_SSC", "OTHER_SSC", "Other", True, []),
    ("PRE_ENGINEERING", "INTERMEDIATE", "FSc Pre-Engineering", False,
     [("MATH", True, None), ("PHY", True, None), ("CHEM", True, None), ("ENG", True, None)]),
    ("PRE_MEDICAL", "INTERMEDIATE", "FSc Pre-Medical", False,
     [("BIO", True, None), ("CHEM", True, None), ("PHY", True, None), ("ENG", True, None)]),
    ("ICS", "INTERMEDIATE", "ICS (Computer Science)", False,
     [("MATH", True, None), ("CS", True, None), ("PHY", False, "ICS_3"),
      ("STAT", False, "ICS_3"), ("ECON", False, "ICS_3"), ("ENG", True, None)]),
    ("ICOM", "INTERMEDIATE", "I.Com (Commerce)", False,
     [("ACCT", True, None), ("COMM", True, None), ("ECON", True, None), ("BMATH", True, None),
      ("ENG", True, None)]),
    ("GENERAL_SCIENCE", "INTERMEDIATE", "General Science", True,
     [("MATH", False, None), ("STAT", False, None), ("ECON", False, None),
      ("PHY", False, None), ("ENG", True, None)]),
    ("FA", "INTERMEDIATE", "FA (Humanities / Arts)", True, [("ENG", True, None)]),
    ("A_LEVEL", "A_LEVEL", "A-Levels", True, []),
    ("OTHER_HSSC", "OTHER_HSSC", "Other", True, []),
    ("DAE_ELECTRICAL", "DAE", "DAE Electrical", False,
     [("MATH", True, None), ("PHY", True, None), ("CHEM", True, None)]),
    ("DAE_ELECTRONICS", "DAE", "DAE Electronics", False,
     [("MATH", True, None), ("PHY", True, None), ("CHEM", True, None)]),
    ("DAE_MECHANICAL", "DAE", "DAE Mechanical", False,
     [("MATH", True, None), ("PHY", True, None), ("CHEM", True, None)]),
    ("DAE_CIVIL", "DAE", "DAE Civil", False,
     [("MATH", True, None), ("PHY", True, None), ("CHEM", True, None)]),
    ("DAE_CIT", "DAE", "DAE Computer Information Technology", False,
     [("MATH", True, None), ("PHY", True, None), ("CHEM", True, None)]),
    ("DAE_CHEMICAL", "DAE", "DAE Chemical", False,
     [("MATH", True, None), ("PHY", True, None), ("CHEM", True, None)]),
]

FIELDS = [
    ("COMPUTING", "Computing & IT", "computer", [
        ("CS", "Computer Science"), ("SE", "Software Engineering"),
        ("AI", "Artificial Intelligence"), ("DS", "Data Science"),
        ("IT", "Information Technology"), ("CYBER", "Cyber Security")]),
    ("ENGINEERING", "Engineering", "engineering", [
        ("EE", "Electrical Engineering"), ("ME", "Mechanical Engineering"),
        ("CE", "Civil Engineering"), ("CPE", "Computer Engineering"),
        ("CHE", "Chemical Engineering")]),
    ("ENG_TECH", "Engineering Technology", "build", [
        ("BSET_EE", "Electrical Engineering Technology"),
        ("BSET_ME", "Mechanical Engineering Technology"),
        ("BSET_CE", "Civil Engineering Technology")]),
    ("MEDICAL", "Medical & Dental", "medical", [("MBBS", "MBBS (Medicine)"), ("BDS", "BDS (Dentistry)")]),
    ("ALLIED_HEALTH", "Allied Health Sciences", "health", [
        ("PHARMD", "Pharm-D (Pharmacy)"), ("DPT", "Doctor of Physical Therapy"),
        ("BSN", "Nursing")]),
    ("BUSINESS", "Business & Management", "business", [
        ("BBA", "Business Administration"), ("ACF", "Accounting & Finance"),
        ("ECON_BS", "Economics")]),
    ("LIFE_SCIENCES", "Life Sciences", "science", [
        ("BIOTECH", "Biotechnology"), ("BIOCHEM", "Biochemistry"), ("MICRO", "Microbiology")]),
    ("NATURAL_SCIENCES", "Natural Sciences & Mathematics", "calculate", [
        ("MATH_BS", "Mathematics"), ("PHY_BS", "Physics"), ("CHEM_BS", "Chemistry")]),
    ("SOCIAL_SCIENCES", "Social Sciences", "groups", [
        ("PSY_BS", "Psychology"), ("IR", "International Relations"),
        ("MASSCOM", "Media & Communication")]),
    ("LAW", "Law", "gavel", [("LLB", "LLB (Law)")]),
    ("EDUCATION", "Education", "school", [("BED", "B.Ed (Education)")]),
]

ENTRY_TESTS = [
    ("ECAT", "Engineering College Admission Test (ECAT)", "UET Lahore"),
    ("MDCAT", "Medical and Dental College Admission Test (MDCAT)", "PM&DC"),
    ("NAT", "National Aptitude Test (NAT)", "National Testing Service (NTS)"),
    ("NET", "NUST Entry Test (NET)", "NUST"),
    ("SAT", "SAT", "College Board"),
    ("UNI_TEST", "University's own admission test", "Each university"),
]


def seed_reference(db: Session) -> None:
    if db.scalar(select(m.Region).limit(1)):
        return
    for i, (code, name, kind) in enumerate(REGIONS):
        db.add(m.Region(code=code, name=name, kind=kind, sort_order=i))
    db.flush()
    for region, name, lat, lon in CITIES:
        db.add(m.City(region_code=region, name=name, latitude=lat, longitude=lon))
    for name, short, kind, region in BOARDS:
        db.add(m.ExamBoard(name=name, short_name=short, kind=kind, region_code=region))
    for i, (code, level, name, ibcc) in enumerate(QUAL_TYPES):
        db.add(m.QualificationType(code=code, level=level, name=name, uses_ibcc=ibcc,
                                   sort_order=i))
    for code, name in SUBJECTS:
        db.add(m.Subject(code=code, name=name))
    db.flush()
    for i, (code, type_code, name, custom, _subjects) in enumerate(GROUPS):
        db.add(m.QualificationGroup(code=code, type_code=type_code, name=name,
                                    allows_custom_subjects=custom, sort_order=i))
    db.flush()
    for code, _type, _name, _custom, subjects in GROUPS:
        for subject, compulsory, choice in subjects:
            db.add(m.GroupSubject(group_code=code, subject_code=subject,
                                  is_compulsory=compulsory, choice_set=choice))
    for i, (code, name, icon, _disciplines) in enumerate(FIELDS):
        db.add(m.ProgrammeField(code=code, name=name, icon=icon, sort_order=i))
    db.flush()
    for code, _name, _icon, disciplines in FIELDS:
        for d_code, d_name in disciplines:
            db.add(m.Discipline(code=d_code, field_code=code, name=d_name))
    for code, name, by in ENTRY_TESTS:
        db.add(m.EntryTest(code=code, name=name, conducted_by=by))
    db.add(m.AdmissionCycle(year=2026, label="Fall 2026", is_current=False))
    db.add(m.AdmissionCycle(year=2027, label="Fall 2027", is_current=True))
    db.add(m.AppSetting(key="result_mode", value={"mode": "extended"}))
    db.commit()


# ============================================================ demo catalogue

HSSC_ANY = {"level": "HSSC"}


def _rule(rule_type: str, params: dict, hard: bool = True) -> dict:
    return {"type": rule_type, "params": params, "hard": hard}


def _accept(*groups: str, level: str = "HSSC", types: list[str] | None = None) -> dict:
    params = {"level": level, "groups": list(groups)}
    if types:
        params["types"] = types
    return _rule("accepted_qualification", params)


def _min(pct: float, level: str = "HSSC") -> dict:
    return _rule("min_percentage", {"level": level, "min": pct})


A_LEVEL_SET = ("For A-Level students", [
    _rule("accepted_qualification", {"level": "HSSC", "types": ["A_LEVEL"]}),
    _rule("required_subjects", {"level": "HSSC", "all_of": ["MATH"]}),
    _min(60), _rule("ibcc_equivalence_required", {"for_types": ["A_LEVEL", "O_LEVEL"]}),
])

DEMO = [
    {
        "name": "Demo University of Engineering & Technology",
        "short": "Demo UET", "sector": "public", "gender": "coeducation",
        "campuses": [{
            "name": "Main Campus", "city": "Lahore", "main": True,
            "hostels": [("male", "on_campus", "available", 18000),
                        ("female", "on_campus", "limited", 18000)],
            "programmes": [
                {"title": "BSc Electrical Engineering", "discipline": "EE", "degree": "BSc_Eng",
                 "acc": ("PEC", "accredited"), "tests": ["ECAT"],
                 "fees": [("admission", 15000, "one_time"), ("tuition", 32000, "per_semester"),
                          ("exam", 3000, "per_semester")],
                 "sets": [
                     ("For FSc Pre-Engineering students", [
                         _accept("PRE_ENGINEERING"),
                         _rule("required_subjects", {"level": "HSSC",
                                                     "all_of": ["MATH", "PHY"]}),
                         _min(60), _rule("entry_test_required", {"tests": ["ECAT"]})]),
                     A_LEVEL_SET,
                 ]},
                {"title": "BS Computer Science", "discipline": "CS", "degree": "BS",
                 "acc": ("NCEAC", "accredited"), "tests": ["ECAT"],
                 "fees": [("admission", 15000, "one_time"), ("tuition", 30000, "per_semester"),
                          ("exam", 3000, "per_semester")],
                 "sets": [
                     ("For Pre-Engineering, ICS and Pre-Medical students", [
                         _accept("PRE_ENGINEERING", "ICS", "PRE_MEDICAL"),
                         _rule("required_subjects", {"level": "HSSC", "all_of": ["MATH"]}),
                         _rule("deficiency_allowed", {
                             "for_groups": ["PRE_MEDICAL"], "missing_subject": "MATH",
                             "course": "Deficiency Mathematics (6 credit hours) in the first year"}),
                         _min(50), _rule("result_status", {"level": "HSSC", "accept_part1": True}),
                         _rule("entry_test_required", {"tests": ["ECAT", "UNI_TEST"]})]),
                 ]},
                {"title": "BSc Electrical Engineering Technology", "discipline": "BSET_EE",
                 "degree": "BSc_Eng_Tech", "acc": ("NTC", "accredited"), "tests": ["UNI_TEST"],
                 "fees": [("admission", 12000, "one_time"), ("tuition", 26000, "per_semester")],
                 "sets": [
                     ("For DAE students", [
                         _accept("DAE_ELECTRICAL", "DAE_ELECTRONICS", level="DIPLOMA"),
                         _min(60, level="DIPLOMA"),
                         _rule("entry_test_required", {"tests": ["UNI_TEST"]})]),
                     ("For FSc Pre-Engineering students", [
                         _accept("PRE_ENGINEERING"), _min(50)]),
                 ]},
            ],
        }],
    },
    {
        "name": "Demo Institute of Business & Computing",
        "short": "Demo IBC", "sector": "private", "gender": "coeducation",
        "campuses": [{
            "name": "Karachi Campus", "city": "Karachi", "main": True,
            "hostels": [("male", "off_campus_university_managed", "limited", 30000),
                        ("female", "on_campus", "not_available", None)],
            "programmes": [
                {"title": "BBA (Hons)", "discipline": "BBA", "degree": "BBA",
                 "acc": ("NBEAC", "accredited"), "tests": ["UNI_TEST"],
                 "fees": [("admission", 25000, "one_time"), ("tuition", 145000, "per_semester")],
                 "sets": [("For all Intermediate and A-Level students", [
                     _rule("accepted_qualification", {"level": "HSSC",
                                                      "types": ["INTERMEDIATE", "A_LEVEL"]}),
                     _min(45), _rule("entry_test_required", {"tests": ["UNI_TEST", "SAT"]}),
                     _rule("manual_note", {"text": "An interview is part of the admission process."}),
                 ])]},
                {"title": "BS Artificial Intelligence", "discipline": "AI", "degree": "BS",
                 "acc": ("NCEAC", "unknown"), "tests": ["UNI_TEST"], "credit_hours": 133,
                 "fees": [("admission", 25000, "one_time"), ("tuition", 9500, "per_credit_hour")],
                 "sets": [("For Pre-Engineering and ICS students", [
                     _accept("PRE_ENGINEERING", "ICS"),
                     _rule("required_subjects", {"level": "HSSC", "all_of": ["MATH"]}),
                     _min(50)]), A_LEVEL_SET]},
                {"title": "BS Computer Science (Evening)", "discipline": "CS", "degree": "BS",
                 "shift": "evening", "acc": ("NCEAC", "accredited"), "tests": ["UNI_TEST"],
                 "fees": [("admission", 20000, "one_time"), ("tuition", 98000, "per_semester")],
                 "sets": [("For Pre-Engineering and ICS students", [
                     _accept("PRE_ENGINEERING", "ICS"), _min(50)])]},
            ],
        }],
    },
    {
        "name": "Demo Women's University",
        "short": "Demo WU", "sector": "public", "gender": "women_only",
        "campuses": [{
            "name": "Peshawar Campus", "city": "Peshawar", "main": True,
            "hostels": [("female", "on_campus", "available", 15000)],
            "programmes": [
                {"title": "BS Computer Science", "discipline": "CS", "degree": "BS",
                 "acc": ("NCEAC", "accredited"), "tests": [],
                 "fees": [("admission", 8000, "one_time"), ("tuition", 22000, "per_semester")],
                 "sets": [("For Pre-Engineering, ICS and General Science students", [
                     _accept("PRE_ENGINEERING", "ICS", "GENERAL_SCIENCE"),
                     _rule("required_subjects", {"level": "HSSC", "all_of": ["MATH"]}),
                     _min(45)])]},
                {"title": "BS Biotechnology", "discipline": "BIOTECH", "degree": "BS",
                 "acc": (None, None), "tests": [],
                 "fees": [("admission", 8000, "one_time"), ("tuition", 24000, "per_semester")],
                 "sets": [("For FSc Pre-Medical students", [
                     _accept("PRE_MEDICAL"),
                     _rule("required_subjects", {"level": "HSSC", "all_of": ["BIO", "CHEM"]}),
                     _min(50)])]},
                {"title": "BBA", "discipline": "BBA", "degree": "BBA",
                 "acc": (None, None), "tests": [],
                 "fees": [("admission", 8000, "one_time"), ("tuition", 20000, "per_semester")],
                 "sets": [("For all Intermediate students", [
                     _rule("accepted_qualification", {"level": "HSSC"}), _min(45)])]},
            ],
        }],
    },
    {
        "name": "Demo College of Medical & Health Sciences",
        "short": "Demo CMHS", "sector": "semi_government", "gender": "coeducation",
        "campuses": [{
            "name": "Islamabad Campus", "city": "Islamabad", "main": True,
            "hostels": [("male", "on_campus", "available", 25000),
                        ("female", "on_campus", "available", 25000)],
            "programmes": [
                {"title": "MBBS", "discipline": "MBBS", "degree": "MBBS", "years": 5,
                 "acc": ("PMDC", "accredited"), "tests": ["MDCAT"],
                 "fees": [("admission", 30000, "one_time"), ("tuition", 210000, "per_year")],
                 "sets": [("For FSc Pre-Medical students", [
                     _accept("PRE_MEDICAL"),
                     _rule("required_subjects", {"level": "HSSC",
                                                 "all_of": ["BIO", "CHEM", "PHY"]}),
                     _min(60),
                     _rule("entry_test_required", {"tests": ["MDCAT"],
                                                   "min_score_percentage": 55})]),
                     ("For A-Level students", [
                         _rule("accepted_qualification", {"level": "HSSC",
                                                          "types": ["A_LEVEL"]}),
                         _rule("required_subjects", {"level": "HSSC",
                                                     "all_of": ["BIO", "CHEM", "PHY"]}),
                         _min(60), _rule("ibcc_equivalence_required", {}),
                         _rule("entry_test_required", {"tests": ["MDCAT"],
                                                       "min_score_percentage": 55})])]},
                {"title": "Doctor of Physical Therapy (DPT)", "discipline": "DPT", "degree": "DPT",
                 "years": 5, "acc": (None, None), "tests": ["UNI_TEST"],
                 "fees": [("admission", 20000, "one_time"), ("tuition", 85000, "per_semester")],
                 "sets": [("For FSc Pre-Medical students", [
                     _accept("PRE_MEDICAL"), _min(50)])]},
            ],
        }],
    },
    {
        # Only has data from the previous cycle: demonstrates the "stale data" warning.
        "name": "Demo University of Balochistan Sciences",
        "short": "Demo UBS", "sector": "public", "gender": "coeducation", "stale": True,
        "campuses": [{
            "name": "Quetta Campus", "city": "Quetta", "main": True,
            "hostels": [("male", "on_campus", "unknown", None)],
            "programmes": [
                {"title": "BS Information Technology", "discipline": "IT", "degree": "BS",
                 "acc": (None, None), "tests": [],
                 "fees": [("admission", 7000, "one_time"), ("tuition", 18000, "per_semester")],
                 "sets": [("For Pre-Engineering and ICS students", [
                     _accept("PRE_ENGINEERING", "ICS"), _min(45),
                     _rule("domicile", {"regions": ["BA"], "seat_type": "regional quota"},
                           hard=False)])]},
            ],
        }],
    },
]


def seed_demo(db: Session) -> None:
    if db.scalar(select(m.University).where(m.University.is_demo).limit(1)):
        return
    cities = {c.name: c for c in db.scalars(select(m.City))}
    cycles = {c.year: c for c in db.scalars(select(m.AdmissionCycle))}
    source = m.Source(kind="demo", title="Demo data - not an official source",
                      is_official=False)
    db.add(source)
    db.flush()
    stamp = datetime(2026, 11, 1, tzinfo=UTC)
    published = {"status": "published", "source_id": source.id, "verified_at": stamp}

    for u in DEMO:
        uni = m.University(
            name=u["name"], short_name=u["short"], aliases=[u["short"]], sector=u["sector"],
            gender_policy=u["gender"], is_demo=True,
            website_url="https://example.com", admissions_url="https://example.com/admissions",
            description="Sample data for testing the app. This is not a real university.",
            **published)
        db.add(uni)
        cycle = cycles[2026 if u.get("stale") else 2027]
        for c in u["campuses"]:
            city = cities[c["city"]]
            campus = m.Campus(university=uni, name=c["name"], is_main_campus=c["main"],
                              city_id=city.id, latitude=city.latitude,
                              longitude=city.longitude, **published)
            db.add(campus)
            for gender, location, availability, fee in c["hostels"]:
                db.add(m.Hostel(campus=campus, for_gender=gender, location=location,
                                availability=availability, fee_per_semester_pkr=fee,
                                **published))
            for p in c["programmes"]:
                body, acc_status = p["acc"]
                programme = m.Programme(
                    campus=campus, discipline_code=p["discipline"], title=p["title"],
                    degree_type=p["degree"], duration_years=p.get("years", 4),
                    total_credit_hours=p.get("credit_hours"), shift=p.get("shift", "morning"),
                    accreditation_body=body, accreditation_status=acc_status, **published)
                db.add(programme)
                offering = m.Offering(programme=programme, cycle_id=cycle.id, seats_total=60,
                                      **published)
                db.add(offering)
                for component, amount, basis in p["fees"]:
                    db.add(m.OfferingFee(offering=offering, component=component,
                                         amount_pkr=amount, basis=basis))
                for test in p["tests"]:
                    db.add(m.OfferingEntryTest(offering=offering, test_code=test))
                db.add(m.OfferingDeadline(offering=offering, event="applications_open",
                                          date=date(cycle.year, 6, 15), is_tentative=True))
                db.add(m.OfferingDeadline(offering=offering, event="applications_close",
                                          date=date(cycle.year, 7, 31), is_tentative=True))
                for priority, (set_name, rules) in enumerate(p["sets"]):
                    rs = m.RuleSetRow(offering=offering, name=set_name, priority=priority)
                    db.add(rs)
                    for r in rules:
                        db.add(m.RuleRow(rule_set=rs, rule_type=r["type"], params=r["params"],
                                         is_hard=r["hard"], source_id=source.id))
    db.commit()
