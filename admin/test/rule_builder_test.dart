import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';
import 'package:unirah_admin/api.dart';
import 'package:unirah_admin/screens/offering_screen.dart';
import 'package:unirah_admin/state.dart';

class _FakeApi extends Api {
  _FakeApi() : super(TokenStore());
  final puts = <String, Object?>{};

  @override
  Future<dynamic> get(String path, [Map<String, dynamic>? query]) async => {
        'id': 'o1',
        'status': 'draft',
        'rules': [],
      };

  @override
  Future<dynamic> put(String path, Object? body) async {
    puts[path] = body;
    return {'message': 'Saved as draft.'};
  }
}

class _FakeSession extends SessionNotifier {
  @override
  Future<Staff?> build() async => Staff('u1', 'editor@example.com', 'data_editor');
}

const _reference = {
  'qualification_types': [
    {'code': 'INTERMEDIATE', 'level': 'HSSC', 'name': 'Intermediate'},
  ],
  'qualification_groups': [
    {'code': 'ICS', 'type_code': 'INTERMEDIATE', 'name': 'ICS'},
  ],
  'subjects': [
    {'code': 'MATH', 'name': 'Mathematics'},
  ],
  'entry_tests': [],
  'regions': [],
};

void main() {
  testWidgets('typing a minimum percentage is saved in the rules', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1200, 2000));
    final api = _FakeApi();
    await tester.pumpWidget(ProviderScope(
      overrides: [
        apiProvider.overrideWithValue(api),
        sessionProvider.overrideWith(_FakeSession.new),
      ],
      child: MaterialApp(
        home: Scaffold(
          body: RuleBuilder(
            offeringId: 'o1',
            initial: const [
              {
                'name': 'For ICS students',
                'rules': [
                  {'rule_type': 'min_percentage', 'is_hard': true, 'params': {'level': 'HSSC', 'min': 50}},
                ],
              },
            ],
            campusGenderPolicy: 'coeducation',
            reference: _reference,
          ),
        ),
      ),
    ));
    await tester.pumpAndSettle();

    final field = find.widgetWithText(TextFormField, 'Minimum %');
    expect(field, findsOneWidget);
    await tester.enterText(field, '55');
    await tester.pump();
    await tester.tap(find.text('Save rules'));
    await tester.pumpAndSettle();

    final body = api.puts['/v1/admin/offerings/o1/rules'] as List;
    final params = ((body.first as Map)['rules'] as List).first['params'] as Map;
    expect(params['min'], 55);
  });
}
