// Data models that mirror the backend JSON. Kept as small, hand-written classes.

typedef Json = Map<String, dynamic>;

List<T> _list<T>(dynamic value, T Function(Json) f) =>
    (value as List? ?? const []).map((e) => f(e as Json)).toList();

List<String> _strings(dynamic value) =>
    (value as List? ?? const []).map((e) => e.toString()).toList();

double? _double(dynamic v) => v == null ? null : (v as num).toDouble();

// ---------------------------------------------------------------- reference

class Named {
  Named(this.code, this.name);
  final String code;
  final String name;
}

class CityRef {
  CityRef(this.id, this.name, this.regionCode);
  final String id;
  final String name;
  final String regionCode;
}

class BoardRef {
  BoardRef(this.id, this.name, this.shortName, this.kind, this.regionCode);
  final String id;
  final String name;
  final String shortName;
  final String kind;
  final String? regionCode;
}

class QualTypeRef {
  QualTypeRef(this.code, this.level, this.name, this.usesIbcc);
  final String code;
  final String level;
  final String name;
  final bool usesIbcc;
}

class GroupSubjectRef {
  GroupSubjectRef(this.code, this.isCompulsory, this.choiceSet);
  final String code;
  final bool isCompulsory;
  final String? choiceSet;
}

class GroupRef {
  GroupRef(this.code, this.typeCode, this.name, this.allowsCustomSubjects, this.subjects);
  final String code;
  final String typeCode;
  final String name;
  final bool allowsCustomSubjects;
  final List<GroupSubjectRef> subjects;
}

class DisciplineRef {
  DisciplineRef(this.code, this.fieldCode, this.name);
  final String code;
  final String fieldCode;
  final String name;
}

class Reference {
  Reference.fromJson(Json j)
      : cycleLabel = (j['current_cycle'] as Json)['label'] as String,
        regions = _list(j['regions'], (e) => Named(e['code'], e['name'])),
        cities = _list(j['cities'], (e) => CityRef(e['id'], e['name'], e['region_code'])),
        boards = _list(j['boards'],
            (e) => BoardRef(e['id'], e['name'], e['short_name'], e['kind'], e['region_code'])),
        types = _list(j['qualification_types'],
            (e) => QualTypeRef(e['code'], e['level'], e['name'], e['uses_ibcc'] as bool)),
        groups = _list(
            j['qualification_groups'],
            (e) => GroupRef(
                e['code'],
                e['type_code'],
                e['name'],
                e['allows_custom_subjects'] as bool,
                _list(e['subjects'],
                    (s) => GroupSubjectRef(s['code'], s['is_compulsory'] as bool, s['choice_set'])))),
        subjects = _list(j['subjects'], (e) => Named(e['code'], e['name'])),
        fields = _list(j['fields'], (e) => Named(e['code'], e['name'])),
        disciplines =
            _list(j['disciplines'], (e) => DisciplineRef(e['code'], e['field_code'], e['name'])),
        tests = _list(j['entry_tests'], (e) => Named(e['code'], e['name']));

  final String cycleLabel;
  final List<Named> regions;
  final List<CityRef> cities;
  final List<BoardRef> boards;
  final List<QualTypeRef> types;
  final List<GroupRef> groups;
  final List<Named> subjects;
  final List<Named> fields;
  final List<DisciplineRef> disciplines;
  final List<Named> tests;

  String subjectName(String code) =>
      subjects.firstWhere((s) => s.code == code, orElse: () => Named(code, code)).name;
  String regionName(String code) =>
      regions.firstWhere((s) => s.code == code, orElse: () => Named(code, code)).name;
  String fieldName(String code) =>
      fields.firstWhere((s) => s.code == code, orElse: () => Named(code, code)).name;
  String disciplineName(String code) => disciplines
      .firstWhere((s) => s.code == code, orElse: () => DisciplineRef(code, '', code))
      .name;
  String groupName(String code) => groups
      .firstWhere((s) => s.code == code, orElse: () => GroupRef(code, '', code, true, []))
      .name;
  String testName(String code) =>
      tests.firstWhere((s) => s.code == code, orElse: () => Named(code, code)).name;
  CityRef? city(String? id) => cities.where((c) => c.id == id).firstOrNull;
  List<QualTypeRef> typesFor(String level) => types.where((t) => t.level == level).toList();
  List<GroupRef> groupsFor(String typeCode) => groups.where((g) => g.typeCode == typeCode).toList();
}

// ---------------------------------------------------------------- auth/profile

class AppUser {
  AppUser.fromJson(Json j)
      : id = j['id'],
        email = j['email'],
        role = j['role'];
  final String id;
  final String email;
  final String role;
}

class SubjectMark {
  SubjectMark(this.code, {this.obtained, this.total});
  SubjectMark.fromJson(Json j)
      : code = j['code'],
        obtained = _double(j['obtained']),
        total = _double(j['total']);
  final String code;
  final double? obtained;
  final double? total;

  Json toJson() => {
        'code': code,
        if (obtained != null) 'obtained': obtained,
        if (total != null) 'total': total,
      };
}

class Qualification {
  Qualification.fromJson(Json j)
      : level = j['level'],
        typeCode = j['type_code'],
        groupCode = j['group_code'],
        boardId = j['board_id'],
        passingYear = j['passing_year'],
        resultStatus = j['result_status'],
        obtained = _double(j['obtained_marks']),
        total = _double(j['total_marks']),
        percentage = _double(j['percentage']),
        part1Obtained = _double(j['part1_obtained']),
        part1Total = _double(j['part1_total']),
        part1Percentage = _double(j['part1_percentage']),
        ibccPercentage = _double(j['ibcc_percentage']),
        ibccIsOfficial = j['ibcc_is_official'] as bool,
        subjects = _list(j['subjects'], SubjectMark.fromJson);

  final String level;
  final String typeCode;
  final String groupCode;
  final String? boardId;
  final int? passingYear;
  final String resultStatus;
  final double? obtained;
  final double? total;
  final double? percentage;
  final double? part1Obtained;
  final double? part1Total;
  final double? part1Percentage;
  final double? ibccPercentage;
  final bool ibccIsOfficial;
  final List<SubjectMark> subjects;
}

class TestScore {
  TestScore.fromJson(Json j)
      : id = j['id'],
        testCode = j['test_code'],
        year = j['year'],
        score = (j['score'] as num).toDouble(),
        total = (j['total'] as num).toDouble();
  final String id;
  final String testCode;
  final int year;
  final double score;
  final double total;
}

class Preferences {
  Preferences({
    this.regions = const [],
    this.cityIds = const [],
    this.maxFeePerSemester,
    this.budgetIncludes = 'university_charges',
    this.sectors = const [],
    this.hostelNeed = 'none',
    this.genderCampusPref = 'any',
    this.shifts = const [],
    this.requireAccreditation = false,
    this.disciplines = const [],
    this.fields = const [],
  });

  Preferences.fromJson(Json j)
      : regions = _strings(j['regions']),
        cityIds = _strings(j['city_ids']),
        maxFeePerSemester = j['max_fee_per_semester'] as int?,
        budgetIncludes = j['budget_includes'] ?? 'university_charges',
        sectors = _strings(j['sectors']),
        hostelNeed = j['hostel_need'] ?? 'none',
        genderCampusPref = j['gender_campus_pref'] ?? 'any',
        shifts = _strings(j['shifts']),
        requireAccreditation = j['require_accreditation'] as bool? ?? false,
        disciplines = _strings(j['disciplines']),
        fields = _strings(j['fields']);

  final List<String> regions;
  final List<String> cityIds;
  final int? maxFeePerSemester;
  final String budgetIncludes;
  final List<String> sectors;
  final String hostelNeed;
  final String genderCampusPref;
  final List<String> shifts;
  final bool requireAccreditation;
  final List<String> disciplines;
  final List<String> fields;

  Preferences copyWith({
    List<String>? regions,
    List<String>? cityIds,
    int? Function()? maxFeePerSemester,
    String? budgetIncludes,
    List<String>? sectors,
    String? hostelNeed,
    String? genderCampusPref,
    List<String>? shifts,
    bool? requireAccreditation,
    List<String>? disciplines,
    List<String>? fields,
  }) =>
      Preferences(
        regions: regions ?? this.regions,
        cityIds: cityIds ?? this.cityIds,
        maxFeePerSemester:
            maxFeePerSemester != null ? maxFeePerSemester() : this.maxFeePerSemester,
        budgetIncludes: budgetIncludes ?? this.budgetIncludes,
        sectors: sectors ?? this.sectors,
        hostelNeed: hostelNeed ?? this.hostelNeed,
        genderCampusPref: genderCampusPref ?? this.genderCampusPref,
        shifts: shifts ?? this.shifts,
        requireAccreditation: requireAccreditation ?? this.requireAccreditation,
        disciplines: disciplines ?? this.disciplines,
        fields: fields ?? this.fields,
      );

  Json toJson() => {
        'regions': regions,
        'city_ids': cityIds,
        'max_fee_per_semester': maxFeePerSemester,
        'budget_includes': budgetIncludes,
        'sectors': sectors,
        'hostel_need': hostelNeed,
        'gender_campus_pref': genderCampusPref,
        'shifts': shifts,
        'require_accreditation': requireAccreditation,
        'disciplines': disciplines,
        'fields': fields,
      };
}

class Completeness {
  Completeness.fromJson(Json j)
      : percent = j['percent'] as int,
        missing = _strings(j['missing']),
        ready = j['ready_for_recommendations'] as bool;
  final int percent;
  final List<String> missing;
  final bool ready;
}

class Profile {
  Profile.fromJson(Json j)
      : fullName = j['full_name'],
        phone = j['phone'],
        gender = j['gender'],
        dateOfBirth = j['date_of_birth'],
        currentCityId = j['current_city_id'],
        domicileRegionCode = j['domicile_region_code'],
        qualifications = _list(j['qualifications'], Qualification.fromJson),
        testScores = _list(j['test_scores'], TestScore.fromJson),
        preferences = Preferences.fromJson(j['preferences'] as Json),
        completeness = Completeness.fromJson(j['completeness'] as Json);

  final String? fullName;
  final String? phone;
  final String? gender;
  final String? dateOfBirth;
  final String? currentCityId;
  final String? domicileRegionCode;
  final List<Qualification> qualifications;
  final List<TestScore> testScores;
  final Preferences preferences;
  final Completeness completeness;

  Qualification? qualification(String level) =>
      qualifications.where((q) => q.level == level).firstOrNull;
  Qualification? get higherSecondary => qualification('HSSC') ?? qualification('DIPLOMA');
}

// ---------------------------------------------------------------- catalogue

class OfferingCard {
  OfferingCard.fromJson(Json j)
      : offeringId = j['offering_id'],
        programmeTitle = j['programme_title'],
        disciplineCode = j['discipline_code'],
        fieldCode = j['field_code'],
        durationYears = _double(j['duration_years']) ?? 4,
        shift = j['shift'],
        universityId = j['university_id'],
        universityName = j['university_name'],
        universityShortName = j['university_short_name'],
        sector = j['sector'],
        isDemo = j['is_demo'] as bool? ?? false,
        campusName = j['campus_name'],
        city = j['city'],
        regionCode = j['region_code'],
        genderPolicy = j['gender_policy'],
        cycleLabel = j['cycle_label'],
        isStale = j['is_stale'] as bool? ?? false,
        tuitionPerSemester = j['tuition_per_semester'] as int?,
        chargesPerSemester = j['charges_per_semester'] as int?,
        firstYearTotal = j['first_year_total'] as int?,
        feeIsEstimated = j['fee_is_estimated'] as bool? ?? false,
        entryTests = _strings(j['entry_tests']),
        hostelFor = _strings(j['hostel_for']),
        accreditationBody = j['accreditation_body'],
        accreditationStatus = j['accreditation_status'],
        applicationsClose = j['applications_close'],
        verifiedAt = j['verified_at'],
        category = j['category'];

  final String offeringId;
  final String programmeTitle;
  final String disciplineCode;
  final String fieldCode;
  final double durationYears;
  final String shift;
  final String universityId;
  final String universityName;
  final String? universityShortName;
  final String sector;
  final bool isDemo;
  final String campusName;
  final String city;
  final String regionCode;
  final String genderPolicy;
  final String cycleLabel;
  final bool isStale;
  final int? tuitionPerSemester;
  final int? chargesPerSemester;
  final int? firstYearTotal;
  final bool feeIsEstimated;
  final List<String> entryTests;
  final List<String> hostelFor;
  final String? accreditationBody;
  final String? accreditationStatus;
  final String? applicationsClose;
  final String? verifiedAt;
  final String? category; // only in shortlist responses
}

class FeeItem {
  FeeItem.fromJson(Json j)
      : component = j['component'],
        amount = j['amount_pkr'] as int,
        basis = j['basis'],
        appliesTo = j['applies_to'];
  final String component;
  final int amount;
  final String basis;
  final String appliesTo;
}

class Hostel {
  Hostel.fromJson(Json j)
      : forGender = j['for_gender'],
        location = j['location'],
        availability = j['availability'],
        feePerSemester = j['fee_per_semester_pkr'] as int?;
  final String forGender;
  final String location;
  final String availability;
  final int? feePerSemester;
}

class RuleSetView {
  RuleSetView.fromJson(Json j)
      : name = j['name'],
        rules = (j['rules'] as List).cast<Json>();
  final String name;
  final List<Json> rules;
}

class OfferingDetail {
  OfferingDetail.fromJson(Json j)
      : card = OfferingCard.fromJson(j),
        seatsTotal = j['seats_total'] as int?,
        notes = j['notes'],
        firstSemesterTotal = (j['fees'] as Json)['first_semester_total'] as int?,
        degreeEstimate = (j['fees'] as Json)['degree_estimate'] as int?,
        feeItems = _list((j['fees'] as Json)['items'], FeeItem.fromJson),
        ruleSets = _list(j['rule_sets'], RuleSetView.fromJson),
        deadlines = (j['deadlines'] as List).cast<Json>(),
        hostels = _list(j['hostels'], Hostel.fromJson),
        websiteUrl = j['website_url'],
        admissionsUrl = j['admissions_url'],
        sourceTitle = (j['source'] as Json?)?['title'],
        sourceIsOfficial = (j['source'] as Json?)?['is_official'] as bool? ?? false;

  final OfferingCard card;
  final int? seatsTotal;
  final String? notes;
  final int? firstSemesterTotal;
  final int? degreeEstimate;
  final List<FeeItem> feeItems;
  final List<RuleSetView> ruleSets;
  final List<Json> deadlines;
  final List<Hostel> hostels;
  final String? websiteUrl;
  final String? admissionsUrl;
  final String? sourceTitle;
  final bool sourceIsOfficial;
}

// ---------------------------------------------------------------- recommendations

class RuleOutcome {
  RuleOutcome.fromJson(Json j)
      : type = j['type'],
        outcome = j['outcome'],
        message = j['message'];
  final String type;
  final String outcome; // pass | fail | unknown
  final String message;
}

class RecommendationResult {
  RecommendationResult.fromJson(Json j)
      : offering = OfferingCard.fromJson(j['offering'] as Json),
        category = j['category'],
        recommended = j['recommended'] as bool,
        ruleSetName = j['rule_set_name'],
        outcomes = _list(j['rule_outcomes'], RuleOutcome.fromJson),
        nextSteps = _strings(j['next_steps']),
        misses = _strings(j['misses']),
        withinPreferences = j['within_preferences'] as bool;

  final OfferingCard offering;
  final String category;
  final bool recommended;
  final String? ruleSetName;
  final List<RuleOutcome> outcomes;
  final List<String> nextSteps;
  final List<String> misses;
  final bool withinPreferences;
}

class NoMatch {
  NoMatch.fromJson(Json j)
      : kind = j['kind'],
        reasons = _list(j['reasons'], (e) => (e['text'] as String, e['count'] as int)),
        disciplineSuggestions = _list(j['discipline_suggestions'],
            (e) => (e['discipline_id'] as String, e['field_id'] as String, e['count'] as int)),
        preferenceSuggestions = _list(j['preference_suggestions'],
            (e) => (e['miss'] as String, e['count'] as int, e['suggested_max_fee'] as int?)),
        qualifyingCount = j['qualifying_count'] as int? ?? 0;

  final String kind; // academic | preferences
  final List<(String, int)> reasons;
  final List<(String, String, int)> disciplineSuggestions;
  final List<(String, int, int?)> preferenceSuggestions;
  final int qualifyingCount;
}

class RecommendationRun {
  RecommendationRun.fromJson(Json j)
      : runId = j['run_id'],
        createdAt = j['created_at'],
        mode = j['mode'],
        isOutdated = j['is_outdated'] as bool,
        cycleLabel = (j['summary'] as Json)['cycle_label'] as String? ?? '',
        hiddenByPreferences = (j['summary'] as Json)['hidden_by_preferences'] as int? ?? 0,
        noMatch = (j['summary'] as Json)['no_match'] == null
            ? null
            : NoMatch.fromJson((j['summary'] as Json)['no_match'] as Json),
        results = _list(j['results'], RecommendationResult.fromJson);

  final String runId;
  final String createdAt;
  final String mode;
  final bool isOutdated;
  final String cycleLabel;
  final int hiddenByPreferences;
  final NoMatch? noMatch;
  final List<RecommendationResult> results;

  bool get strict => mode == 'strict_pdf';

  List<RecommendationResult> group(String category, {bool includeHidden = false}) => results
      .where((r) => r.category == category && (includeHidden || r.withinPreferences))
      .toList();

  List<RecommendationResult> get hidden =>
      results.where((r) => r.recommended && !r.withinPreferences).toList();
}

class EligibilityCheck {
  EligibilityCheck.fromJson(Json j)
      : category = j['category'],
        ruleSetName = j['rule_set_name'],
        outcomes = _list(j['rule_outcomes'], RuleOutcome.fromJson),
        nextSteps = _strings(j['next_steps']);
  final String? category;
  final String? ruleSetName;
  final List<RuleOutcome> outcomes;
  final List<String> nextSteps;
}

class UniversitySummary {
  UniversitySummary.fromJson(Json j)
      : id = j['id'],
        name = j['name'],
        sector = j['sector'],
        isDemo = j['is_demo'] as bool,
        cities = _strings(j['cities']);
  final String id;
  final String name;
  final String sector;
  final bool isDemo;
  final List<String> cities;
}

class UniversityDetail {
  UniversityDetail.fromJson(Json j)
      : id = j['id'],
        name = j['name'],
        sector = j['sector'],
        isDemo = j['is_demo'] as bool,
        genderPolicy = j['gender_policy'],
        description = j['description'],
        websiteUrl = j['website_url'],
        admissionsUrl = j['admissions_url'],
        verifiedAt = j['verified_at'],
        campuses = (j['campuses'] as List).cast<Json>(),
        programmes = _list(j['programmes'], OfferingCard.fromJson);
  final String id;
  final String name;
  final String sector;
  final bool isDemo;
  final String genderPolicy;
  final String? description;
  final String? websiteUrl;
  final String? admissionsUrl;
  final String? verifiedAt;
  final List<Json> campuses;
  final List<OfferingCard> programmes;
}
