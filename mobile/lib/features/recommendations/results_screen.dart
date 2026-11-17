import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../core/format.dart';
import '../../data/models.dart';
import '../../state/providers.dart';
import '../../widgets/common.dart';

/// Results grouped by eligibility (FR-04), with the two no-match paths
/// from docs/RECOMMENDATION_ENGINE.md § 0 and § 4.
class ResultsScreen extends ConsumerWidget {
  const ResultsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recs = ref.watch(recommendationsProvider);
    return recs.when(
      loading: () => Scaffold(
        appBar: AppBar(title: const Text('Your results')),
        body: const Center(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Checking programmes against their published requirements...'),
          ]),
        ),
      ),
      error: (e, _) => Scaffold(
        appBar: AppBar(title: const Text('Your results')),
        body: ErrorView(e, onRetry: () => ref.read(recommendationsProvider.notifier).run()),
      ),
      data: (run) => run == null ? const _NoRunYet() : _Results(run),
    );
  }
}

class _NoRunYet extends ConsumerWidget {
  const _NoRunYet();

  @override
  Widget build(BuildContext context, WidgetRef ref) => Scaffold(
        appBar: AppBar(title: const Text('Your results')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Text('You have not searched yet.'),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: () => ref.read(recommendationsProvider.notifier).run(),
                child: const Text('Find my universities'),
              ),
            ]),
          ),
        ),
      );
}

class _Results extends ConsumerStatefulWidget {
  const _Results(this.run);
  final RecommendationRun run;

  @override
  ConsumerState<_Results> createState() => _ResultsState();
}

class _ResultsState extends ConsumerState<_Results> {
  bool _showHidden = false;

  @override
  Widget build(BuildContext context) {
    final run = widget.run;
    final tabs = [
      ('eligible', 'Eligible'),
      if (!run.strict) ('potentially_eligible', 'Potentially'),
      ('not_eligible', 'Not currently'),
    ];
    return DefaultTabController(
      length: tabs.length,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Your results'),
          actions: [
            IconButton(
              tooltip: 'Edit preferences',
              icon: const Icon(Icons.tune),
              onPressed: () => context.push('/edit/preferences'),
            ),
            IconButton(
              tooltip: 'Search again',
              icon: const Icon(Icons.refresh),
              onPressed: () => ref.read(recommendationsProvider.notifier).run(),
            ),
          ],
          bottom: run.noMatch == null
              ? TabBar(tabs: [
                  for (final (cat, label) in tabs)
                    Tab(text: '$label (${run.group(cat, includeHidden: cat == 'not_eligible' || _showHidden).length})'),
                ])
              : null,
        ),
        body: Column(children: [
          if (run.isOutdated)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              child: Row(children: [
                const Expanded(
                    child: InfoBanner('Your profile changed since this search.', icon: Icons.update)),
                const SizedBox(width: 8),
                FilledButton(
                    onPressed: () => ref.read(recommendationsProvider.notifier).run(),
                    child: const Text('Update')),
              ]),
            ),
          Expanded(
            child: run.noMatch != null
                ? _NoMatchView(run)
                : TabBarView(children: [
                    for (final (cat, _) in tabs) _list(run, cat),
                  ]),
          ),
        ]),
      ),
    );
  }

  Widget _list(RecommendationRun run, String category) {
    final notEligible = category == 'not_eligible';
    final items = run.group(category, includeHidden: notEligible || _showHidden);
    return ListView(padding: const EdgeInsets.all(16), children: [
      Text('Based on ${run.cycleLabel} data. ${notEligible ? 'These programmes are shown so you can see why.' : 'Sorted by best match with your preferences.'}',
          style: Theme.of(context).textTheme.bodySmall),
      const SizedBox(height: 8),
      if (!notEligible) const NoGuaranteeNote(),
      if (category == 'potentially_eligible')
        const Padding(
          padding: EdgeInsets.only(top: 8),
          child: InfoBanner(
              'You do not fail any known requirement here, but something still needs to be '
              'confirmed. Open each one to see what.',
              icon: Icons.help_outline),
        ),
      const SizedBox(height: 12),
      if (items.isEmpty)
        const Padding(
          padding: EdgeInsets.symmetric(vertical: 32),
          child: Text('Nothing in this group.', textAlign: TextAlign.center),
        ),
      for (final r in items)
        Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: OfferingTile(
            r.offering,
            category: r.category,
            onTap: () => context.push('/programme/${r.offering.offeringId}'),
            footer: _whyLine(r),
          ),
        ),
      if (!notEligible && run.hiddenByPreferences > 0)
        Center(
          child: TextButton.icon(
            icon: Icon(_showHidden ? Icons.visibility_off : Icons.visibility),
            label: Text(_showHidden
                ? 'Hide options outside my preferences'
                : 'Show ${run.hiddenByPreferences} more outside my preferences'),
            onPressed: () => setState(() => _showHidden = !_showHidden),
          ),
        ),
    ]);
  }

  Widget? _whyLine(RecommendationResult r) {
    final s = Theme.of(context).colorScheme;
    final lines = <Widget>[];
    final firstIssue = r.outcomes.where((o) => o.outcome != 'pass').firstOrNull;
    if (firstIssue != null) {
      lines.add(Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        OutcomeIcon(firstIssue.outcome),
        const SizedBox(width: 6),
        Expanded(child: Text(firstIssue.message, style: Theme.of(context).textTheme.bodySmall)),
      ]));
    }
    if (!r.withinPreferences && r.misses.isNotEmpty) {
      lines.add(Text('Outside your preferences: ${r.misses.map(missLabel).join(', ')}',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: s.error)));
    }
    if (lines.isEmpty) return null;
    return Padding(
      padding: const EdgeInsets.only(top: 10),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, spacing: 4, children: lines),
    );
  }
}

class _NoMatchView extends ConsumerWidget {
  const _NoMatchView(this.run);
  final RecommendationRun run;

  Future<void> _applyAndRerun(WidgetRef ref, Preferences p) async {
    await ref.read(profileProvider.notifier).savePreferences(p);
    await ref.read(recommendationsProvider.notifier).run();
  }

  Preferences _relax(Preferences p, String miss, int? fee) => switch (miss) {
        'over_budget' => p.copyWith(maxFeePerSemester: () => fee),
        'outside_location' => p.copyWith(regions: [], cityIds: []),
        'sector' => p.copyWith(sectors: []),
        'no_hostel' => p.copyWith(hostelNeed: p.hostelNeed == 'on_campus_only' ? 'needed' : 'none'),
        'campus_type' => p.copyWith(genderCampusPref: 'any'),
        'shift' => p.copyWith(shifts: []),
        'not_accredited' => p.copyWith(requireAccreditation: false),
        _ => p,
      };

  String _suggestionText(String miss, int count, int? fee) {
    final options = '$count option${count == 1 ? '' : 's'}';
    return switch (miss) {
      'over_budget' => 'Raise budget to ${pkr(fee)} per semester → $options',
      'outside_location' => 'Include all provinces and regions → $options',
      'sector' => 'Include all university types → $options',
      'no_hostel' => 'Change hostel need → $options',
      'campus_type' => 'Allow any campus type → $options',
      'shift' => 'Allow any class timing → $options',
      'not_accredited' => 'Include programmes without accreditation → $options',
      _ => '${missLabel(miss)} → $options',
    };
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final nm = run.noMatch!;
    final reference = ref.watch(referenceProvider).value;
    final profile = ref.watch(profileProvider).value;
    final t = Theme.of(context).textTheme;

    if (nm.kind == 'preferences') {
      return ListView(padding: const EdgeInsets.all(16), children: [
        Text('No options match all your preferences', style: t.titleLarge),
        const SizedBox(height: 8),
        Text('You meet the requirements for ${nm.qualifyingCount} programme'
            '${nm.qualifyingCount == 1 ? '' : 's'}, but none fit all your preferences. '
            'Try one of these changes:'),
        const SizedBox(height: 16),
        for (final (miss, count, fee) in nm.preferenceSuggestions)
          Card(
            margin: const EdgeInsets.only(bottom: 8),
            child: ListTile(
              leading: const Icon(Icons.tune),
              title: Text(_suggestionText(miss, count, fee)),
              trailing: const Icon(Icons.chevron_right),
              onTap: profile == null
                  ? null
                  : () => _applyAndRerun(ref, _relax(profile.preferences, miss, fee)),
            ),
          ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          icon: const Icon(Icons.edit),
          label: const Text('Edit preferences'),
          onPressed: () => context.push('/edit/preferences'),
        ),
        TextButton(
          onPressed: () => context.push('/results/all'),
          child: Text('Show all ${nm.qualifyingCount} anyway'),
        ),
      ]);
    }

    // Academic no-match: changing budget or location cannot help, so we don't suggest it.
    return ListView(padding: const EdgeInsets.all(16), children: [
      Text('No programmes in your chosen fields match your background', style: t.titleLarge),
      if (nm.reasons.isNotEmpty) ...[
        const SizedBox(height: 12),
        Text('Main reasons', style: t.titleSmall),
        for (final (text, count) in nm.reasons)
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const OutcomeIcon('fail'),
            title: Text(text),
            subtitle: Text('$count programme${count == 1 ? '' : 's'}'),
          ),
      ],
      if (nm.disciplineSuggestions.isNotEmpty && reference != null) ...[
        const SizedBox(height: 12),
        Text('You may consider', style: t.titleSmall),
        const SizedBox(height: 8),
        for (final (discipline, field, count) in nm.disciplineSuggestions)
          Card(
            margin: const EdgeInsets.only(bottom: 8),
            child: ListTile(
              leading: const Icon(Icons.lightbulb_outline),
              title: Text(reference.disciplineName(discipline)),
              subtitle: Text('${reference.fieldName(field)} · $count option${count == 1 ? '' : 's'}'),
              trailing: const Icon(Icons.chevron_right),
              onTap: profile == null
                  ? null
                  : () => _applyAndRerun(
                      ref,
                      profile.preferences.copyWith(
                        fields: {...profile.preferences.fields, field}.toList(),
                        disciplines: [
                          ...profile.preferences.disciplines,
                          if (profile.preferences.disciplines.isNotEmpty) discipline,
                        ],
                      )),
            ),
          ),
      ],
      const SizedBox(height: 12),
      OutlinedButton.icon(
        icon: const Icon(Icons.interests),
        label: const Text('Change my fields'),
        onPressed: () => context.push('/edit/interests'),
      ),
      const SizedBox(height: 8),
      OutlinedButton.icon(
        icon: const Icon(Icons.school),
        label: const Text('Check my marks and subjects'),
        onPressed: () => context.push('/edit/qualification/HSSC'),
      ),
    ]);
  }
}

/// "Show all anyway": every qualifying option, ignoring preferences.
class AllQualifyingScreen extends ConsumerWidget {
  const AllQualifyingScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final run = ref.watch(recommendationsProvider).value;
    final items = run?.results.where((r) => r.recommended).toList() ?? [];
    return Scaffold(
      appBar: AppBar(title: const Text('All options you qualify for')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        const InfoBanner('These do not fit all your preferences.'),
        const SizedBox(height: 12),
        for (final r in items)
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: OfferingTile(
              r.offering,
              category: r.category,
              onTap: () => context.push('/programme/${r.offering.offeringId}'),
              footer: Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text('Outside your preferences: ${r.misses.map(missLabel).join(', ')}',
                    style: Theme.of(context).textTheme.bodySmall),
              ),
            ),
          ),
      ]),
    );
  }
}
