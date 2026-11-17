import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';
import 'package:unirah/core/format.dart';
import 'package:unirah/data/models.dart';
import 'package:unirah/features/auth/auth_screens.dart';
import 'package:unirah/features/explore/programme_screen.dart';
import 'package:unirah/widgets/common.dart';

Reference _reference() => Reference.fromJson({
      'current_cycle': {'year': 2027, 'label': 'Fall 2027'},
      'regions': [
        {'code': 'PB', 'name': 'Punjab', 'kind': 'province'}
      ],
      'cities': [],
      'boards': [],
      'qualification_types': [],
      'qualification_groups': [
        {'code': 'ICS', 'type_code': 'INTERMEDIATE', 'name': 'ICS (Computer Science)',
         'allows_custom_subjects': false, 'subjects': []},
        {'code': 'PRE_MEDICAL', 'type_code': 'INTERMEDIATE', 'name': 'FSc Pre-Medical',
         'allows_custom_subjects': false, 'subjects': []},
      ],
      'subjects': [
        {'code': 'MATH', 'name': 'Mathematics'}
      ],
      'fields': [],
      'disciplines': [],
      'entry_tests': [
        {'code': 'ECAT', 'name': 'ECAT', 'conducted_by': 'UET'}
      ],
    });

Map<String, dynamic> _card() => {
      'offering_id': 'o1', 'programme_title': 'BS Computer Science', 'discipline_code': 'CS',
      'field_code': 'COMPUTING', 'duration_years': 4.0, 'shift': 'morning', 'university_id': 'u1',
      'university_name': 'Demo University', 'university_short_name': 'DU', 'sector': 'public',
      'is_demo': true, 'campus_name': 'Main Campus', 'city': 'Lahore', 'region_code': 'PB',
      'gender_policy': 'coeducation', 'cycle_label': 'Fall 2026', 'is_stale': true,
      'charges_per_semester': 33000, 'entry_tests': ['ECAT'], 'hostel_for': ['male'],
    };

void main() {
  test('rules are described in plain English', () {
    final r = _reference();
    expect(
      describeRule({'type': 'accepted_qualification',
        'params': {'level': 'HSSC', 'groups': ['ICS', 'PRE_MEDICAL']}}, r),
      'Accepted backgrounds: ICS (Computer Science) or FSc Pre-Medical.',
    );
    expect(describeRule({'type': 'min_percentage', 'params': {'level': 'HSSC', 'min': 60}}, r),
        'At least 60% in Intermediate / A-Level.');
    expect(describeRule({'type': 'deficiency_allowed', 'params': {
      'for_groups': ['PRE_MEDICAL'], 'course': 'Deficiency Maths'}}, r),
        'FSc Pre-Medical students can join with: Deficiency Maths.');
  });

  test('money and percentages are formatted for students', () {
    expect(pkr(75000), 'PKR 75,000');
    expect(pkr(null), 'Not available');
    expect(percent(60.0), '60%');
    expect(percent(72.456), '72.46%');
  });

  testWidgets('status is shown with words, not colour alone', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: StatusChip('potentially_eligible'))));
    expect(find.text('Potentially eligible'), findsOneWidget);
  });

  testWidgets('demo data and stale data are clearly labelled', (tester) async {
    await tester.pumpWidget(MaterialApp(
        home: Scaffold(body: OfferingTile(OfferingCard.fromJson(_card()), category: 'eligible'))));
    expect(find.text('SAMPLE DATA'), findsOneWidget);
    expect(find.text('Data from Fall 2026'), findsOneWidget);
    expect(find.text('Eligible'), findsOneWidget);
  });

  testWidgets('welcome screen states that admission is not guaranteed', (tester) async {
    await tester.binding.setSurfaceSize(const Size(500, 1400));
    await tester.pumpWidget(const MaterialApp(home: WelcomeScreen()));
    expect(find.textContaining('does not guarantee admission'), findsOneWidget);
    expect(find.text('Create account'), findsOneWidget);
  });
}
