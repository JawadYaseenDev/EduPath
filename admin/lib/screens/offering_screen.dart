// One programme in one admission cycle: details, eligibility rules, fees, tests, dates.
import 'dart:convert';

import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../api.dart';
import '../state.dart';
import '../widgets.dart';

final _offeringProvider = FutureProvider.autoDispose.family<Json, String>((ref, id) async {
  ref.watch(refreshProvider);
  return await ref.watch(apiProvider).get('/v1/admin/offerings/$id') as Json;
});

class OfferingScreen extends ConsumerWidget {
  const OfferingScreen({super.key, required this.id});
  final String id;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(_offeringProvider(id));
    final reference = ref.watch(referenceProvider).value;
    return AsyncBody(
      data,
      builder: (o) {
        final uni = o['university'] as Json;
        final programme = o['programme'] as Json;
        final campus = o['campus'] as Json;
        final pending = (o['pending_changes'] as List).cast<Json>();
        final unpublishedParents = [
          if (uni['status'] != 'published') 'university',
          if (campus['status'] != 'published') 'campus',
          if (programme['status'] != 'published') 'programme',
        ];
        return DefaultTabController(
          length: 5,
          child: PageScaffold(
            title: '${programme['title']} · ${o['cycle_label']}',
            breadcrumb: TextButton.icon(
              onPressed: () => context.go('/universities/${uni['id']}'),
              icon: const Icon(Icons.arrow_back, size: 16),
              label: Text('${uni['name']} · ${campus['name']}'),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(24, 12, 24, 0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      WorkflowActions(entityType: 'offering', entityId: id, status: o['status'] as String),
                      if (o['review_note'] != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(
                            'Reviewer note: ${o['review_note']}',
                            style: TextStyle(color: Theme.of(context).colorScheme.error),
                          ),
                        ),
                      if (o['carried_from_cycle_id'] != null && o['status'] != 'published')
                        const _Note(
                          'Copied from last year. Check every value against this year\'s official '
                          'prospectus and choose the new source before submitting.',
                          icon: Icons.content_copy,
                        ),
                      if (unpublishedParents.isNotEmpty)
                        _Note(
                          'Students will not see this programme until the ${unpublishedParents.join(', ')} '
                          '${unpublishedParents.length == 1 ? 'is' : 'are'} also published.',
                          icon: Icons.visibility_off,
                        ),
                      PendingChangesNote(pending.length),
                    ],
                  ),
                ),
                const TabBar(
                  isScrollable: true,
                  tabs: [
                    Tab(text: 'Eligibility rules'),
                    Tab(text: 'Fees'),
                    Tab(text: 'Entry tests'),
                    Tab(text: 'Dates'),
                    Tab(text: 'Details & review'),
                  ],
                ),
                Expanded(
                  child: TabBarView(
                    children: [
                      RuleBuilder(
                        key: ValueKey('rules-${jsonEncode(o['rules'])}'),
                        offeringId: id,
                        initial: (o['rules'] as List).cast<Json>(),
                        campusGenderPolicy: campus['gender_policy'] as String,
                        reference: reference,
                      ),
                      _FeesTab(key: ValueKey('fees-${jsonEncode(o['fees'])}'), offering: o),
                      _TestsTab(key: ValueKey('tests-${jsonEncode(o['tests'])}'), offering: o, reference: reference),
                      _DeadlinesTab(key: ValueKey('dl-${jsonEncode(o['deadlines'])}'), offering: o),
                      _DetailsTab(offering: o, pending: pending),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _Note extends StatelessWidget {
  const _Note(this.text, {required this.icon});
  final String text;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final s = Theme.of(context).colorScheme;
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(color: s.secondaryContainer, borderRadius: BorderRadius.circular(8)),
      child: Row(
        children: [
          Icon(icon, size: 18, color: s.onSecondaryContainer),
          const SizedBox(width: 8),
          Expanded(
            child: Text(text, style: TextStyle(color: s.onSecondaryContainer)),
          ),
        ],
      ),
    );
  }
}

/// Save button shared by the tabs. Explains that live records go to review.
Widget _saveBar(BuildContext context, Json offering, VoidCallback onSave, {String label = 'Save'}) {
  final live = offering['status'] == 'published';
  return Padding(
    padding: const EdgeInsets.only(top: 16),
    child: Row(
      children: [
        FilledButton.icon(
          onPressed: onSave,
          icon: const Icon(Icons.save),
          label: Text(live ? 'Save for review' : label),
        ),
        const SizedBox(width: 12),
        if (live)
          const Expanded(
            child: Text(
              'This programme is live. Your change will be shown to students after a '
              'verifier approves it.',
            ),
          ),
      ],
    ),
  );
}

// ================================================================== rule builder

enum P {
  level,
  groups,
  types,
  subjects,
  subjectGroups,
  subject,
  number,
  integer,
  tests,
  genders,
  regions,
  text,
  toggle,
  date,
}

typedef ParamSpec = (String key, P kind, String label);

const _level = ('level', P.level, 'Applies to');

/// Plain-English names and fields for each rule type (backend: app/engine/rules.py).
const Map<String, (String, String, List<ParamSpec>)> ruleSpecs = {
  'accepted_qualification': (
    'Accepted backgrounds',
    'Which qualifications and groups can apply.',
    [
      _level,
      ('types', P.types, 'Qualification types (leave empty for any)'),
      ('groups', P.groups, 'Groups / streams (leave empty for any)'),
    ],
  ),
  'required_subjects': (
    'Required subjects',
    'Subjects the student must have studied.',
    [
      _level,
      ('all_of', P.subjects, 'Must have ALL of these'),
      ('one_of', P.subjectGroups, 'Must have at least ONE from each of these groups'),
    ],
  ),
  'min_percentage': (
    'Minimum percentage',
    'Lowest accepted marks percentage.',
    [_level, ('min', P.number, 'Minimum %'), ('accept_part1', P.toggle, 'Students can apply with Part-I marks')],
  ),
  'min_subject_marks': (
    'Minimum marks in a subject',
    'e.g. at least 60% in Mathematics.',
    [_level, ('subject', P.subject, 'Subject'), ('min_percentage', P.number, 'Minimum % in this subject')],
  ),
  'entry_test_required': (
    'Entry test',
    'The student must take one of these tests.',
    [('tests', P.tests, 'Any of these tests'), ('min_score_percentage', P.number, 'Minimum score % (optional)')],
  ),
  'deficiency_allowed': (
    'Deficiency course route',
    'A group can join if it completes an extra course.',
    [
      ('for_groups', P.groups, 'Groups allowed with a deficiency course'),
      ('missing_subject', P.subject, 'Subject they are missing (optional)'),
      ('course', P.text, 'Course they must complete'),
    ],
  ),
  'result_status': (
    'Part-I marks accepted',
    'Students waiting for their final result may apply.',
    [_level, ('accept_part1', P.toggle, 'Part-I marks accepted')],
  ),
  'ibcc_equivalence_required': (
    'IBCC certificate required',
    'For A-Level / O-Level students.',
    [('for_types', P.types, 'For these qualification types')],
  ),
  'gender': ('Gender restriction', 'Only these students may apply.', [('allowed', P.genders, 'Open to')]),
  'domicile': (
    'Domicile / quota seats',
    'Seats reserved by domicile.',
    [('regions', P.regions, 'Domicile of'), ('seat_type', P.text, 'Seat type, e.g. regional quota')],
  ),
  'max_age': (
    'Age limit',
    'Maximum age on a date.',
    [('years', P.integer, 'Maximum age (years)'), ('on_date', P.date, 'On date (YYYY-MM-DD)')],
  ),
  'passing_year_window': (
    'Passing year',
    'Only recent pass-outs.',
    [_level, ('min_year', P.integer, 'Passed in this year or later')],
  ),
  'improved_result_policy': (
    'Improved results',
    'Whether supplementary / improved results count.',
    [('accepted', P.toggle, 'Improved results accepted')],
  ),
  'manual_note': (
    'Needs manual check',
    'Always shows "potentially eligible" with this note.',
    [('text', P.text, 'Note shown to students, e.g. "Interview required"')],
  ),
};

Json _defaults(String type) {
  final params = <String, dynamic>{};
  for (final (key, kind, _) in ruleSpecs[type]!.$3) {
    params[key] = switch (kind) {
      P.level => 'HSSC',
      P.groups || P.types || P.subjects || P.subjectGroups || P.tests || P.genders || P.regions => <dynamic>[],
      P.toggle => false,
      _ => null,
    };
  }
  if (type == 'ibcc_equivalence_required') params['for_types'] = ['A_LEVEL', 'O_LEVEL'];
  if (type == 'result_status') params['accept_part1'] = true;
  return params;
}

/// Drop empty optional values before sending, so the backend applies its defaults.
Json _clean(Json params) => {
  for (final e in params.entries)
    if (e.value != null && !(e.value is String && (e.value as String).trim().isEmpty)) e.key: e.value,
};

class RuleBuilder extends ConsumerStatefulWidget {
  const RuleBuilder({
    super.key,
    required this.offeringId,
    required this.initial,
    required this.campusGenderPolicy,
    required this.reference,
  });
  final String offeringId;
  final List<Json> initial;
  final String campusGenderPolicy;
  final Json? reference;

  @override
  ConsumerState<RuleBuilder> createState() => _RuleBuilderState();
}

class _RuleBuilderState extends ConsumerState<RuleBuilder> {
  late final List<Json> _sets = [
    for (final rs in widget.initial)
      {
        'name': rs['name'],
        'rules': [
          for (final r in (rs['rules'] as List).cast<Json>())
            {
              'rule_type': r['rule_type'],
              'is_hard': r['is_hard'],
              'params': {..._defaults(r['rule_type']), ...(r['params'] as Json)},
            },
        ],
      },
  ];
  List<Json>? _testResults;
  bool _dirty = false;

  List<Json> get _payload => [
    for (final rs in _sets)
      {
        'name': rs['name'],
        'rules': [
          for (final r in (rs['rules'] as List).cast<Json>())
            {'rule_type': r['rule_type'], 'is_hard': r['is_hard'], 'params': _clean(r['params'] as Json)},
        ],
      },
  ];

  void _changed() => setState(() {
    _dirty = true;
    _testResults = null;
  });

  Future<void> _test() async {
    try {
      final r = await ref.read(apiProvider).post('/v1/admin/rules/test', {
        'rule_sets': _payload,
        'campus_gender_policy': widget.campusGenderPolicy,
      });
      setState(() => _testResults = (r as List).cast<Json>());
    } catch (e) {
      if (mounted) toast(context, e.toString(), error: true);
    }
  }

  Future<void> _save(Json offering) async {
    final ok = await runAction(
      context,
      ref,
      () => ref.read(apiProvider).put('/v1/admin/offerings/${widget.offeringId}/rules', _payload),
    );
    if (ok) setState(() => _dirty = false);
  }

  @override
  Widget build(BuildContext context) {
    final offering = ref.watch(_offeringProvider(widget.offeringId)).value ?? const {};
    final canEdit = ref.watch(sessionProvider).value?.canEdit ?? false;
    // A Column (not a lazy ListView) keeps every field alive while scrolling, so typed
    // values are never lost when a rule card scrolls out of view.
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'A student is eligible if they meet ALL rules in ANY ONE group. Use one group per '
            'background, e.g. "For FSc Pre-Engineering students" and "For ICS students". '
            '"Must pass" rules make the student not eligible when failed; "Check only" rules make them '
            'potentially eligible.',
          ),
          const SizedBox(height: 16),
          for (var i = 0; i < _sets.length; i++) _ruleSetCard(i, canEdit),
          if (canEdit)
            Align(
              alignment: Alignment.centerLeft,
              child: OutlinedButton.icon(
                icon: const Icon(Icons.add),
                label: const Text('Add rule group'),
                onPressed: () {
                  _sets.add({'name': '', 'rules': <Json>[]});
                  _changed();
                },
              ),
            ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              OutlinedButton.icon(
                icon: const Icon(Icons.science_outlined),
                label: const Text('Test with sample students'),
                onPressed: _sets.isEmpty ? null : _test,
              ),
              if (canEdit) _saveBar(context, offering, () => _save(offering), label: 'Save rules'),
              if (_dirty) Text('Unsaved changes', style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
          ),
          if (_testResults != null) _TestResults(_testResults!),
        ],
      ),
    );
  }

  Widget _ruleSetCard(int i, bool canEdit) {
    final rs = _sets[i];
    final rules = (rs['rules'] as List).cast<Json>();
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    initialValue: rs['name'] as String,
                    enabled: canEdit,
                    decoration: InputDecoration(labelText: 'Group ${i + 1} name', hintText: 'e.g. For ICS students'),
                    onChanged: (v) {
                      rs['name'] = v;
                      _changed();
                    },
                  ),
                ),
                if (canEdit)
                  IconButton(
                    tooltip: 'Remove group',
                    icon: const Icon(Icons.delete_outline),
                    onPressed: () {
                      _sets.removeAt(i);
                      _changed();
                    },
                  ),
              ],
            ),
            const SizedBox(height: 12),
            for (var j = 0; j < rules.length; j++) _ruleEditor(rules, j, canEdit),
            if (canEdit)
              MenuAnchor(
                menuChildren: [
                  for (final e in ruleSpecs.entries)
                    MenuItemButton(
                      onPressed: () {
                        rules.add({'rule_type': e.key, 'is_hard': e.key != 'manual_note', 'params': _defaults(e.key)});
                        _changed();
                      },
                      child: SizedBox(
                        width: 360,
                        child: ListTile(dense: true, title: Text(e.value.$1), subtitle: Text(e.value.$2)),
                      ),
                    ),
                ],
                builder: (_, controller, _) => TextButton.icon(
                  icon: const Icon(Icons.add),
                  label: const Text('Add rule'),
                  onPressed: () => controller.isOpen ? controller.close() : controller.open(),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _ruleEditor(List<Json> rules, int j, bool canEdit) {
    final r = rules[j];
    final spec = ruleSpecs[r['rule_type']];
    final params = r['params'] as Json;
    final s = Theme.of(context).colorScheme;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: s.outlineVariant),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(spec?.$1 ?? r['rule_type'] as String, style: Theme.of(context).textTheme.titleSmall),
              ),
              SegmentedButton<bool>(
                showSelectedIcon: false,
                segments: const [
                  ButtonSegment(value: true, label: Text('Must pass')),
                  ButtonSegment(value: false, label: Text('Check only')),
                ],
                selected: {r['is_hard'] as bool},
                onSelectionChanged: canEdit
                    ? (v) {
                        r['is_hard'] = v.first;
                        _changed();
                      }
                    : null,
              ),
              if (canEdit)
                IconButton(
                  tooltip: 'Remove rule',
                  icon: const Icon(Icons.close),
                  onPressed: () {
                    rules.removeAt(j);
                    _changed();
                  },
                ),
            ],
          ),
          if (spec != null) ...[
            Text(spec.$2, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 8),
            for (final (key, kind, label) in spec.$3)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: _ParamField(
                  key: ObjectKey((params, key)),
                  kind: kind,
                  label: label,
                  value: params[key],
                  level: params['level'] as String?,
                  reference: widget.reference,
                  enabled: canEdit,
                  onChanged: (v) {
                    params[key] = v;
                    _changed();
                  },
                ),
              ),
          ],
        ],
      ),
    );
  }
}

class _ParamField extends StatelessWidget {
  const _ParamField({
    super.key,
    required this.kind,
    required this.label,
    required this.value,
    required this.level,
    required this.reference,
    required this.enabled,
    required this.onChanged,
  });
  final P kind;
  final String label;
  final dynamic value;
  final String? level;
  final Json? reference;
  final bool enabled;
  final ValueChanged<dynamic> onChanged;

  List<Json> _ref(String key) => ((reference?[key] as List?) ?? const []).cast<Json>();

  Map<String, String> _options() {
    final types = _ref('qualification_types');
    final levelOf = {for (final t in types) t['code']: t['level']};
    return switch (kind) {
      P.types => {
        for (final t in types)
          if (level == null || t['level'] == level) t['code'] as String: t['name'] as String,
      },
      P.groups => {
        for (final g in _ref('qualification_groups'))
          if (level == null || levelOf[g['type_code']] == level) g['code'] as String: g['name'] as String,
      },
      P.subjects || P.subject => {for (final s in _ref('subjects')) s['code'] as String: s['name'] as String},
      P.tests => {for (final t in _ref('entry_tests')) t['code'] as String: t['name'] as String},
      P.regions => {for (final r in _ref('regions')) r['code'] as String: r['name'] as String},
      P.genders => const {'female': 'Female', 'male': 'Male', 'other': 'Other'},
      P.level => const {'SSC': 'Matric / O-Level', 'HSSC': 'Intermediate / A-Level', 'DIPLOMA': 'DAE'},
      _ => const {},
    };
  }

  Widget _multi(Map<String, String> options, List<dynamic> selected, ValueChanged<List<dynamic>> changed) => Wrap(
    spacing: 6,
    runSpacing: 6,
    children: [
      for (final e in options.entries)
        FilterChip(
          label: Text(e.value),
          selected: selected.contains(e.key),
          onSelected: enabled
              ? (on) => changed(on ? [...selected, e.key] : selected.where((v) => v != e.key).toList())
              : null,
        ),
    ],
  );

  @override
  Widget build(BuildContext context) {
    final labelText = Text(label, style: Theme.of(context).textTheme.labelLarge);
    switch (kind) {
      case P.level:
        return Row(
          children: [
            labelText,
            const SizedBox(width: 12),
            DropdownButton<String>(
              value: value as String?,
              items: [for (final e in _options().entries) DropdownMenuItem(value: e.key, child: Text(e.value))],
              onChanged: enabled ? onChanged : null,
            ),
          ],
        );
      case P.subject:
        return Row(
          children: [
            labelText,
            const SizedBox(width: 12),
            DropdownButton<String?>(
              value: value as String?,
              hint: const Text('Choose'),
              items: [
                const DropdownMenuItem<String?>(value: null, child: Text('-')),
                for (final e in _options().entries) DropdownMenuItem(value: e.key, child: Text(e.value)),
              ],
              onChanged: enabled ? onChanged : null,
            ),
          ],
        );
      case P.toggle:
        return SwitchListTile(
          contentPadding: EdgeInsets.zero,
          title: Text(label),
          value: value as bool? ?? false,
          onChanged: enabled ? onChanged : null,
        );
      case P.groups || P.types || P.subjects || P.tests || P.genders || P.regions:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [labelText, const SizedBox(height: 6), _multi(_options(), (value as List?) ?? const [], onChanged)],
        );
      case P.subjectGroups:
        final groups = ((value as List?) ?? const []).map((g) => (g as List).toList()).toList();
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            labelText,
            for (var i = 0; i < groups.length; i++)
              Container(
                margin: const EdgeInsets.only(top: 6),
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: _multi(_options(), groups[i], (v) {
                        groups[i] = v;
                        onChanged(groups);
                      }),
                    ),
                    if (enabled)
                      IconButton(
                        tooltip: 'Remove this group',
                        icon: const Icon(Icons.close),
                        onPressed: () => onChanged([...groups]..removeAt(i)),
                      ),
                  ],
                ),
              ),
            if (enabled)
              TextButton.icon(
                icon: const Icon(Icons.add, size: 18),
                label: const Text('Add "one of" group'),
                onPressed: () => onChanged([...groups, <dynamic>[]]),
              ),
          ],
        );
      case P.number || P.integer || P.text || P.date:
        final numeric = kind == P.number || kind == P.integer;
        return SizedBox(
          width: kind == P.text ? 520 : 260,
          child: TextFormField(
            initialValue: value?.toString() ?? '',
            enabled: enabled,
            decoration: InputDecoration(labelText: label, isDense: true),
            keyboardType: numeric ? const TextInputType.numberWithOptions(decimal: true) : null,
            inputFormatters: kind == P.integer
                ? [FilteringTextInputFormatter.digitsOnly]
                : kind == P.number
                ? [FilteringTextInputFormatter.allow(RegExp(r'[0-9.]'))]
                : null,
            onChanged: (t) {
              final s = t.trim();
              onChanged(switch (kind) {
                P.number => s.isEmpty ? null : double.tryParse(s),
                P.integer => s.isEmpty ? null : int.tryParse(s),
                _ => s,
              });
            },
          ),
        );
    }
  }
}

class _TestResults extends StatelessWidget {
  const _TestResults(this.rows);
  final List<Json> rows;

  @override
  Widget build(BuildContext context) {
    final s = Theme.of(context).colorScheme;
    String label(String? c) => switch (c) {
      'eligible' => 'Eligible',
      'potentially_eligible' => 'Potentially eligible',
      'not_eligible' => 'Not eligible',
      _ => 'No rules',
    };
    Color colour(String? c) => switch (c) {
      'eligible' => s.primary,
      'potentially_eligible' => s.tertiary,
      _ => s.error,
    };
    return Card(
      margin: const EdgeInsets.only(top: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Results for sample students (rules as shown above, not yet saved)',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 8),
            Table(
              columnWidths: const {0: FlexColumnWidth(2), 1: FlexColumnWidth(1.2), 2: FlexColumnWidth(3)},
              children: [
                for (final r in rows)
                  TableRow(
                    children: [
                      Padding(padding: const EdgeInsets.all(6), child: Text(r['student'] as String)),
                      Padding(
                        padding: const EdgeInsets.all(6),
                        child: Text(
                          label(r['category'] as String?),
                          style: TextStyle(color: colour(r['category'] as String?), fontWeight: FontWeight.w600),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.all(6),
                        child: Text((r['reasons'] as List).join('\n'), style: Theme.of(context).textTheme.bodySmall),
                      ),
                    ],
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// ================================================================== fees

class _FeesTab extends ConsumerStatefulWidget {
  const _FeesTab({super.key, required this.offering});
  final Json offering;
  @override
  ConsumerState<_FeesTab> createState() => _FeesTabState();
}

class _FeesTabState extends ConsumerState<_FeesTab> {
  late final List<Json> _rows = [
    for (final f in (widget.offering['fees'] as List).cast<Json>()) {...f},
  ];

  static const _components = {
    'admission': 'Admission',
    'tuition': 'Tuition',
    'registration': 'Registration',
    'exam': 'Exam',
    'library': 'Library',
    'lab': 'Lab',
    'security_refundable': 'Security (refundable)',
    'other': 'Other',
  };
  static const _bases = {
    'one_time': 'One time',
    'per_semester': 'Per semester',
    'per_year': 'Per year',
    'per_credit_hour': 'Per credit hour',
  };

  @override
  Widget build(BuildContext context) {
    final canEdit = ref.watch(sessionProvider).value?.canEdit ?? false;
    final summary = widget.offering['fee_summary'] as Json;
    final programme = widget.offering['programme'] as Json;
    String pkr(dynamic v) => v == null ? '-' : 'PKR $v';
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        if (_rows.any((r) => r['basis'] == 'per_credit_hour') && programme['total_credit_hours'] == null)
          const _Note(
            'Per-credit-hour fees need the programme\'s total credit hours. Add it on the '
            'university page, or totals cannot be calculated.',
            icon: Icons.warning_amber,
          ),
        const SizedBox(height: 8),
        for (var i = 0; i < _rows.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Wrap(
              spacing: 12,
              runSpacing: 8,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                DropdownButton<String>(
                  value: _rows[i]['component'] as String,
                  items: [for (final e in _components.entries) DropdownMenuItem(value: e.key, child: Text(e.value))],
                  onChanged: canEdit ? (v) => setState(() => _rows[i]['component'] = v) : null,
                ),
                SizedBox(
                  width: 160,
                  child: TextFormField(
                    initialValue: '${_rows[i]['amount_pkr']}',
                    enabled: canEdit,
                    inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                    decoration: const InputDecoration(labelText: 'Amount (PKR)', isDense: true),
                    onChanged: (v) => _rows[i]['amount_pkr'] = int.tryParse(v) ?? 0,
                  ),
                ),
                DropdownButton<String>(
                  value: _rows[i]['basis'] as String,
                  items: [for (final e in _bases.entries) DropdownMenuItem(value: e.key, child: Text(e.value))],
                  onChanged: canEdit ? (v) => setState(() => _rows[i]['basis'] = v) : null,
                ),
                DropdownButton<String>(
                  value: _rows[i]['applies_to'] as String,
                  items: const [
                    DropdownMenuItem(value: 'all', child: Text('Every semester / year')),
                    DropdownMenuItem(value: 'first_only', child: Text('First semester only')),
                  ],
                  onChanged: canEdit ? (v) => setState(() => _rows[i]['applies_to'] = v) : null,
                ),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Checkbox(
                      value: _rows[i]['is_estimated'] as bool,
                      onChanged: canEdit ? (v) => setState(() => _rows[i]['is_estimated'] = v ?? false) : null,
                    ),
                    const Text('Estimated'),
                  ],
                ),
                if (canEdit)
                  IconButton(
                    tooltip: 'Remove',
                    icon: const Icon(Icons.delete_outline),
                    onPressed: () => setState(() => _rows.removeAt(i)),
                  ),
              ],
            ),
          ),
        if (canEdit)
          Align(
            alignment: Alignment.centerLeft,
            child: TextButton.icon(
              icon: const Icon(Icons.add),
              label: const Text('Add fee item'),
              onPressed: () => setState(
                () => _rows.add({
                  'component': 'tuition',
                  'amount_pkr': 0,
                  'basis': 'per_semester',
                  'applies_to': 'all',
                  'is_estimated': false,
                }),
              ),
            ),
          ),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Wrap(
              spacing: 32,
              runSpacing: 8,
              children: [
                Text('Saved totals:', style: Theme.of(context).textTheme.titleSmall),
                Text('Per semester: ${pkr(summary['charges_per_semester'])}'),
                Text('First semester: ${pkr(summary['first_semester_total'])}'),
                Text('First year: ${pkr(summary['first_year_total'])}'),
                Text('Whole degree: ${pkr(summary['degree_estimate'])}'),
              ],
            ),
          ),
        ),
        if (canEdit)
          _saveBar(
            context,
            widget.offering,
            () => runAction(
              context,
              ref,
              () => ref.read(apiProvider).put('/v1/admin/offerings/${widget.offering['id']}/fees', _rows),
            ),
            label: 'Save fees',
          ),
      ],
    );
  }
}

// ================================================================== tests

class _TestsTab extends ConsumerStatefulWidget {
  const _TestsTab({super.key, required this.offering, required this.reference});
  final Json offering;
  final Json? reference;
  @override
  ConsumerState<_TestsTab> createState() => _TestsTabState();
}

class _TestsTabState extends ConsumerState<_TestsTab> {
  late final Map<String, bool> _selected = {
    for (final t in (widget.offering['tests'] as List).cast<Json>())
      t['test_code'] as String: t['is_mandatory'] as bool,
  };

  @override
  Widget build(BuildContext context) {
    final canEdit = ref.watch(sessionProvider).value?.canEdit ?? false;
    final tests = ((widget.reference?['entry_tests'] as List?) ?? const []).cast<Json>();
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const Text(
          'Tests listed here are shown on the programme page. To make a test part of '
          'eligibility, also add an "Entry test" rule.',
        ),
        const SizedBox(height: 8),
        for (final t in tests)
          CheckboxListTile(
            value: _selected.containsKey(t['code']),
            title: Text(t['name'] as String),
            subtitle: Text('Conducted by ${t['conducted_by']}'),
            onChanged: canEdit
                ? (on) =>
                      setState(() => on == true ? _selected[t['code'] as String] = true : _selected.remove(t['code']))
                : null,
          ),
        if (canEdit)
          _saveBar(
            context,
            widget.offering,
            () => runAction(
              context,
              ref,
              () => ref.read(apiProvider).put('/v1/admin/offerings/${widget.offering['id']}/tests', [
                for (final e in _selected.entries) {'test_code': e.key, 'is_mandatory': e.value},
              ]),
            ),
            label: 'Save tests',
          ),
      ],
    );
  }
}

// ================================================================== deadlines

class _DeadlinesTab extends ConsumerStatefulWidget {
  const _DeadlinesTab({super.key, required this.offering});
  final Json offering;
  @override
  ConsumerState<_DeadlinesTab> createState() => _DeadlinesTabState();
}

class _DeadlinesTabState extends ConsumerState<_DeadlinesTab> {
  late final List<Json> _rows = [
    for (final d in (widget.offering['deadlines'] as List).cast<Json>()) {...d},
  ];
  static const _events = {
    'applications_open': 'Applications open',
    'applications_close': 'Applications close',
    'test_date': 'Test date',
    'merit_list': 'Merit list',
    'classes_start': 'Classes start',
  };

  @override
  Widget build(BuildContext context) {
    final canEdit = ref.watch(sessionProvider).value?.canEdit ?? false;
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        for (var i = 0; i < _rows.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Wrap(
              spacing: 12,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                DropdownButton<String>(
                  value: _rows[i]['event'] as String,
                  items: [for (final e in _events.entries) DropdownMenuItem(value: e.key, child: Text(e.value))],
                  onChanged: canEdit ? (v) => setState(() => _rows[i]['event'] = v) : null,
                ),
                OutlinedButton.icon(
                  icon: const Icon(Icons.event),
                  label: Text(_rows[i]['date'] as String),
                  onPressed: canEdit
                      ? () async {
                          final picked = await showDatePicker(
                            context: context,
                            initialDate: DateTime.tryParse(_rows[i]['date'] as String) ?? DateTime.now(),
                            firstDate: DateTime(2020),
                            lastDate: DateTime(2100),
                          );
                          if (picked != null) {
                            setState(() => _rows[i]['date'] = picked.toIso8601String().substring(0, 10));
                          }
                        }
                      : null,
                ),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Checkbox(
                      value: _rows[i]['is_tentative'] as bool,
                      onChanged: canEdit ? (v) => setState(() => _rows[i]['is_tentative'] = v ?? false) : null,
                    ),
                    const Text('Tentative'),
                  ],
                ),
                if (canEdit)
                  IconButton(
                    tooltip: 'Remove',
                    icon: const Icon(Icons.delete_outline),
                    onPressed: () => setState(() => _rows.removeAt(i)),
                  ),
              ],
            ),
          ),
        if (canEdit)
          Align(
            alignment: Alignment.centerLeft,
            child: TextButton.icon(
              icon: const Icon(Icons.add),
              label: const Text('Add date'),
              onPressed: () => setState(
                () => _rows.add({
                  'event': 'applications_close',
                  'date': DateTime.now().toIso8601String().substring(0, 10),
                  'is_tentative': true,
                }),
              ),
            ),
          ),
        if (canEdit)
          _saveBar(
            context,
            widget.offering,
            () => runAction(
              context,
              ref,
              () => ref.read(apiProvider).put('/v1/admin/offerings/${widget.offering['id']}/deadlines', _rows),
            ),
            label: 'Save dates',
          ),
      ],
    );
  }
}

// ================================================================== details & pending changes

class _DetailsTab extends ConsumerWidget {
  const _DetailsTab({required this.offering, required this.pending});
  final Json offering;
  final List<Json> pending;

  static const _fields = [
    FieldSpec(
      'is_offered',
      'Offered this cycle',
      FieldKind.toggle,
      help: 'Turn off if the programme is not offered this year. It will not be recommended.',
    ),
    FieldSpec('seats_total', 'Total seats', FieldKind.integer),
    FieldSpec('notes', 'Notes for students', FieldKind.multiline),
    FieldSpec('source_id', 'Source', FieldKind.source),
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final staff = ref.watch(sessionProvider).value;
    final sources = ref.watch(sourcesProvider).value ?? const [];
    final source = sources.where((s) => s['id'] == offering['source_id']).firstOrNull;
    final api = ref.read(apiProvider);
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Wrap(
          spacing: 32,
          runSpacing: 12,
          children: [
            _kv(context, 'Offered this cycle', offering['is_offered'] == true ? 'Yes' : 'No'),
            _kv(context, 'Seats', '${offering['seats_total'] ?? '-'}'),
            _kv(context, 'Source', source == null ? 'Not set' : '${source['title']}'),
            _kv(context, 'Last edited by', '${offering['edited_by_email'] ?? '-'}'),
            _kv(context, 'Last verified', shortDate(offering['verified_at'])),
          ],
        ),
        if (offering['notes'] != null)
          Padding(padding: const EdgeInsets.only(top: 12), child: Text('${offering['notes']}')),
        const SizedBox(height: 12),
        if (staff?.canEdit ?? false)
          Align(
            alignment: Alignment.centerLeft,
            child: OutlinedButton.icon(
              icon: const Icon(Icons.edit),
              label: const Text('Edit details'),
              onPressed: () async {
                final v = await showFormDialog(context, title: 'Edit details', fields: _fields, initial: offering);
                if (v != null && context.mounted) {
                  await runAction(
                    context,
                    ref,
                    () => api.put('/v1/admin/offerings/${offering['id']}', {for (final f in _fields) f.key: v[f.key]}),
                  );
                }
              },
            ),
          ),
        const SizedBox(height: 24),
        Text('Changes waiting for review', style: Theme.of(context).textTheme.titleMedium),
        if (pending.isEmpty) const Text('None.'),
        for (final c in pending) ChangeCard(change: c),
      ],
    );
  }

  Widget _kv(BuildContext context, String k, String v) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(k, style: Theme.of(context).textTheme.labelMedium),
      Text(v),
    ],
  );
}

/// Shows a proposed change as before / after, with approve and reject buttons.
class ChangeCard extends ConsumerWidget {
  const ChangeCard({super.key, required this.change, this.showLink = false});
  final Json change;
  final bool showLink;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final staff = ref.watch(sessionProvider).value;
    final api = ref.read(apiProvider);
    const encoder = JsonEncoder.withIndent('  ');
    Widget box(String title, dynamic value) => Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.labelLarge),
          Container(
            width: double.infinity,
            margin: const EdgeInsets.only(top: 4),
            padding: const EdgeInsets.all(8),
            color: Theme.of(context).colorScheme.surfaceContainerHighest,
            constraints: const BoxConstraints(maxHeight: 320),
            child: SingleChildScrollView(
              child: SelectableText(
                encoder.convert(value),
                style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
              ),
            ),
          ),
        ],
      ),
    );
    return Card(
      margin: const EdgeInsets.only(top: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              change['summary'] as String? ?? titleCase(change['kind'] as String?),
              style: Theme.of(context).textTheme.titleSmall,
            ),
            if (change['label'] != null) Text(change['label'] as String),
            if (change['author_email'] != null)
              Text(
                'Proposed by ${change['author_email']} · ${shortDate(change['created_at'] as String?)}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                box('Now (published)', change['before']),
                const SizedBox(width: 12),
                box('Proposed', change['payload']),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: [
                if (showLink && change['entity_type'] == 'offering')
                  TextButton(
                    onPressed: () => context.go('/offerings/${change['entity_id']}'),
                    child: const Text('Open programme'),
                  ),
                if (staff?.canVerify ?? false) ...[
                  FilledButton.icon(
                    icon: const Icon(Icons.verified, size: 18),
                    label: const Text('Approve'),
                    onPressed: () =>
                        runAction(context, ref, () => api.post('/v1/admin/changes/${change['id']}/approve')),
                  ),
                  OutlinedButton(
                    onPressed: () async {
                      final note = await askText(context, 'Reject change', 'Why is this change wrong?');
                      if (note != null && context.mounted) {
                        await runAction(
                          context,
                          ref,
                          () => api.post('/v1/admin/changes/${change['id']}/reject', {'note': note}),
                        );
                      }
                    },
                    child: const Text('Reject'),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}
