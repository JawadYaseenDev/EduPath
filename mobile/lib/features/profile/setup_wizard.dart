import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../core/format.dart';
import '../../data/models.dart';
import '../../state/providers.dart';
import '../../widgets/common.dart';
import 'forms.dart';

/// First-time profile setup in small steps (FR-02, UI plan § 3.2).
/// Each step saves when the student taps Next, so nothing is lost.
class SetupWizard extends ConsumerStatefulWidget {
  const SetupWizard({super.key});

  @override
  ConsumerState<SetupWizard> createState() => _SetupWizardState();
}

class _SetupWizardState extends ConsumerState<SetupWizard> {
  int _step = 0;
  bool _running = false;

  static const _titles = [
    'About you',
    'Matric / O-Levels',
    'Intermediate / A-Levels / DAE',
    'Entry tests (optional)',
    'Your interests',
    'Your preferences',
    'Review',
  ];

  void _next() => setState(() => _step = (_step + 1).clamp(0, _titles.length - 1));

  Future<void> _findUniversities() async {
    setState(() => _running = true);
    await ref.read(recommendationsProvider.notifier).run();
    if (!mounted) return;
    setState(() => _running = false);
    final result = ref.read(recommendationsProvider);
    if (result.hasError) {
      showMessage(context, result.error.toString());
    } else {
      context.go('/results');
    }
  }

  @override
  Widget build(BuildContext context) {
    final profile = ref.watch(profileProvider);
    final reference = ref.watch(referenceProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(_titles[_step]),
        leading: _step == 0
            ? IconButton(
                tooltip: 'Close',
                icon: const Icon(Icons.close),
                onPressed: () => context.go('/home'))
            : BackButton(onPressed: () => setState(() => _step--)),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(28),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: Row(children: [
              Text('Step ${_step + 1} of ${_titles.length}',
                  style: Theme.of(context).textTheme.labelMedium),
              const SizedBox(width: 12),
              Expanded(child: LinearProgressIndicator(value: (_step + 1) / _titles.length)),
            ]),
          ),
        ),
      ),
      body: switch ((profile, reference)) {
        (AsyncData(value: final p), AsyncData(value: final r)) => Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 640),
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [_body(p, r)],
              ),
            ),
          ),
        (AsyncError(:final error), _) || (_, AsyncError(:final error)) => ErrorView(error,
            onRetry: () {
            ref.invalidate(profileProvider);
            ref.invalidate(referenceProvider);
          }),
        _ => const Loading(),
      },
    );
  }

  Widget _body(Profile p, Reference r) {
    final key = ValueKey('step-$_step');
    switch (_step) {
      case 0:
        return PersonalForm(key: key, profile: p, reference: r, onDone: _next, submitLabel: 'Next');
      case 1:
        return QualificationForm(
            key: key, slot: 'SSC', profile: p, reference: r, onDone: _next, submitLabel: 'Next');
      case 2:
        return QualificationForm(
            key: key, slot: 'HSSC', profile: p, reference: r, onDone: _next, submitLabel: 'Next');
      case 3:
        return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          TestScoresForm(key: key, profile: p, reference: r),
          const SizedBox(height: 12),
          OutlinedButton(onPressed: _next, child: const Text('Next')),
        ]);
      case 4:
        return InterestsForm(key: key, profile: p, reference: r, onDone: _next, submitLabel: 'Next');
      case 5:
        return PreferencesForm(key: key, profile: p, reference: r, onDone: _next, submitLabel: 'Next');
      default:
        return _Review(
          profile: p,
          reference: r,
          running: _running,
          onEdit: (step) => setState(() => _step = step),
          onFind: _findUniversities,
        );
    }
  }
}

class _Review extends StatelessWidget {
  const _Review({required this.profile, required this.reference, required this.running,
      required this.onEdit, required this.onFind});
  final Profile profile;
  final Reference reference;
  final bool running;
  final void Function(int step) onEdit;
  final VoidCallback onFind;

  String _qual(Qualification? q) {
    if (q == null) return 'Not added';
    final group = reference.groupName(q.groupCode);
    final pct = q.ibccPercentage != null
        ? 'IBCC ${percent(q.ibccPercentage)}${q.ibccIsOfficial ? '' : ' (estimated)'}'
        : q.resultStatus == 'part1_only'
            ? 'Part-I ${percent(q.part1Percentage)}'
            : q.resultStatus == 'awaited'
                ? 'Result awaited'
                : percent(q.percentage);
    return '$group · $pct';
  }

  @override
  Widget build(BuildContext context) {
    final prefs = profile.preferences;
    final city = reference.city(profile.currentCityId);
    final rows = <(String, String, int)>[
      ('About you', '${profile.fullName ?? '-'} · ${city?.name ?? 'No city'}', 0),
      ('Matric / O-Levels', _qual(profile.qualification('SSC')), 1),
      ('Intermediate / A-Levels / DAE', _qual(profile.higherSecondary), 2),
      ('Entry tests', profile.testScores.isEmpty ? 'None' : '${profile.testScores.length} added', 3),
      ('Interests', prefs.fields.map(reference.fieldName).join(', '), 4),
      (
        'Preferences',
        [
          prefs.regions.isEmpty ? 'All regions' : prefs.regions.map(reference.regionName).join(', '),
          prefs.maxFeePerSemester == null ? 'No budget limit' : 'Up to ${pkr(prefs.maxFeePerSemester)}/sem',
        ].join(' · '),
        5
      ),
    ];
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      for (final (title, value, step) in rows)
        Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            title: Text(title),
            subtitle: Text(value.isEmpty ? '-' : value),
            trailing: TextButton(onPressed: () => onEdit(step), child: const Text('Edit')),
          ),
        ),
      const SizedBox(height: 12),
      const NoGuaranteeNote(),
      const SizedBox(height: 20),
      FilledButton.icon(
        onPressed: running || !profile.completeness.ready ? null : onFind,
        icon: running
            ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
            : const Icon(Icons.search),
        label: const Text('Find my universities'),
      ),
      if (!profile.completeness.ready)
        const Padding(
          padding: EdgeInsets.only(top: 8),
          child: Text('Please complete "About you" and your Intermediate / A-Level / DAE record first.',
              textAlign: TextAlign.center),
        ),
    ]);
  }
}
