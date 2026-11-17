import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../core/format.dart';
import '../../data/models.dart';
import '../../state/providers.dart';
import '../../widgets/common.dart';

/// Programme details + "why" explanation (FR-04 explain, FR-05 details, FR-06 guidance).
class ProgrammeScreen extends ConsumerStatefulWidget {
  const ProgrammeScreen({super.key, required this.offeringId});
  final String offeringId;

  @override
  ConsumerState<ProgrammeScreen> createState() => _ProgrammeScreenState();
}

class _ProgrammeScreenState extends ConsumerState<ProgrammeScreen> {
  EligibilityCheck? _check;
  bool _checking = false;

  Future<void> _checkMine() async {
    setState(() => _checking = true);
    try {
      final c = await ref.read(apiProvider).myEligibility(widget.offeringId);
      setState(() => _check = c);
    } catch (e) {
      if (mounted) showMessage(context, e.toString());
    } finally {
      if (mounted) setState(() => _checking = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final detail = ref.watch(offeringProvider(widget.offeringId));
    final signedIn = ref.watch(authProvider).status == AuthStatus.signedIn;
    return Scaffold(
      appBar: AppBar(title: const Text('Programme'), actions: [
        if (signedIn) _SaveButton(widget.offeringId),
      ]),
      body: detail.when(
        loading: () => const Loading(),
        error: (e, _) => ErrorView(e, onRetry: () => ref.invalidate(offeringProvider(widget.offeringId))),
        data: (d) => _body(d, signedIn),
      ),
    );
  }

  Widget _body(OfferingDetail d, bool signedIn) {
    final c = d.card;
    final t = Theme.of(context).textTheme;
    final reference = ref.watch(referenceProvider).value;
    final runResult = ref
        .watch(recommendationsProvider)
        .value
        ?.results
        .where((r) => r.offering.offeringId == c.offeringId)
        .firstOrNull;

    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 720),
        child: ListView(padding: const EdgeInsets.all(16), children: [
          if (c.isDemo) ...[
            const InfoBanner('Sample data for testing. This is not a real university or programme.',
                icon: Icons.science_outlined),
            const SizedBox(height: 12),
          ],
          Text(c.programmeTitle, style: t.headlineSmall),
          const SizedBox(height: 4),
          InkWell(
            onTap: () => context.push('/university/${c.universityId}'),
            child: Text(c.universityName,
                style: t.titleMedium?.copyWith(color: Theme.of(context).colorScheme.primary)),
          ),
          Text('${c.campusName} · ${c.city} · ${sectorLabel(c.sector)}'),
          const SizedBox(height: 8),
          Wrap(spacing: 8, runSpacing: 4, children: [
            Chip(label: Text('${c.durationYears.toStringAsFixed(0)} years')),
            Chip(label: Text(shiftLabel(c.shift))),
            Chip(label: Text(genderPolicyLabel(c.genderPolicy))),
            if (c.accreditationBody != null)
              Chip(label: Text('${c.accreditationBody}: ${titleCase(c.accreditationStatus ?? 'unknown')}')),
          ]),
          if (c.isStale)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: InfoBanner(
                  'This information is from ${c.cycleLabel}. This year\'s requirements are not '
                  'confirmed yet. Check the official website.',
                  icon: Icons.history,
                  warning: true),
            ),

          // ---------------------------------------------------------- eligibility
          const SectionTitle('Your eligibility'),
          if (runResult != null)
            _EligibilityCard(
                category: runResult.category,
                ruleSetName: runResult.ruleSetName,
                outcomes: runResult.outcomes,
                nextSteps: runResult.nextSteps,
                misses: runResult.misses)
          else if (_check != null && _check!.category != null)
            _EligibilityCard(
                category: _check!.category!,
                ruleSetName: _check!.ruleSetName,
                outcomes: _check!.outcomes,
                nextSteps: _check!.nextSteps)
          else if (signedIn)
            OutlinedButton.icon(
              onPressed: _checking ? null : _checkMine,
              icon: const Icon(Icons.fact_check_outlined),
              label: Text(_checking ? 'Checking...' : 'Check my eligibility'),
            )
          else
            OutlinedButton(
                onPressed: () => context.go('/register'),
                child: const Text('Create an account to check your eligibility')),

          // ---------------------------------------------------------- requirements
          const SectionTitle('Admission requirements'),
          if (d.ruleSets.isEmpty) const Text('Eligibility details are not available yet.'),
          for (final rs in d.ruleSets)
            Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(rs.name, style: t.titleSmall),
                  const SizedBox(height: 6),
                  for (final text in [
                    if (reference != null)
                      for (final rule in rs.rules) ?describeRule(rule, reference),
                  ])
                      Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          const Text('•  '),
                          Expanded(child: Text(text)),
                        ]),
                      ),
                ]),
              ),
            ),
          if (d.ruleSets.length > 1)
            Text('You need to meet the requirements of any one of these groups.', style: t.bodySmall),

          // ---------------------------------------------------------- fees
          const SectionTitle('Fees'),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(children: [
                for (final f in d.feeItems)
                  _Row(titleCase(f.component),
                      '${pkr(f.amount)} ${feeBasisLabel(f.basis)}${f.appliesTo == 'first_only' ? ' (first semester)' : ''}'),
                const Divider(),
                _Row('Per semester (estimate)', pkr(c.chargesPerSemester), bold: true),
                _Row('First semester total', pkr(d.firstSemesterTotal)),
                _Row('First year total', pkr(c.firstYearTotal)),
                _Row('Whole degree (estimate)', pkr(d.degreeEstimate)),
                if (c.feeIsEstimated)
                  Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: Text('Some totals are estimated (e.g. from per-credit-hour fees).',
                        style: t.bodySmall),
                  ),
              ]),
            ),
          ),

          // ---------------------------------------------------------- tests, deadlines, hostel
          if (c.entryTests.isNotEmpty) ...[
            const SectionTitle('Entry test'),
            for (final code in c.entryTests)
              ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.edit_note),
                  title: Text(reference?.testName(code) ?? code)),
          ],
          if (d.deadlines.isNotEmpty) ...[
            const SectionTitle('Important dates'),
            for (final dl in d.deadlines)
              _Row(titleCase(dl['event'] as String),
                  '${niceDate(dl['date'] as String)}${dl['is_tentative'] == true ? ' (tentative)' : ''}'),
          ],
          const SectionTitle('Hostel'),
          if (d.hostels.isEmpty) const Text('No hostel information available.'),
          for (final h in d.hostels)
            _Row(h.forGender == 'female' ? 'Girls' : 'Boys',
                '${titleCase(h.availability)} · ${hostelLocationLabel(h.location)}'
                '${h.feePerSemester != null ? ' · ${pkr(h.feePerSemester)}/sem' : ''}'),

          // ---------------------------------------------------------- source & links
          const SectionTitle('Source'),
          Text('${d.sourceTitle ?? 'Source not recorded'}'
              '${c.verifiedAt != null ? ' · Last verified ${niceDate(c.verifiedAt)}' : ''}',
              style: t.bodySmall),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: () => openLink(context, d.admissionsUrl ?? d.websiteUrl),
            icon: const Icon(Icons.open_in_new),
            label: const Text('Open official admission page'),
          ),
          const SizedBox(height: 8),
          if (signedIn)
            TextButton.icon(
              onPressed: () => _report(context, c),
              icon: const Icon(Icons.flag_outlined),
              label: const Text('Report incorrect information'),
            ),
          const SizedBox(height: 8),
          const NoGuaranteeNote(),
        ]),
      ),
    );
  }

  Future<void> _report(BuildContext context, OfferingCard c) async {
    final controller = TextEditingController();
    final message = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Report incorrect information'),
        content: TextField(
          controller: controller,
          maxLines: 4,
          decoration: const InputDecoration(hintText: 'What is wrong? e.g. "Fee is now PKR 40,000"'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(ctx, controller.text), child: const Text('Send')),
        ],
      ),
    );
    controller.dispose();
    if (message == null || message.trim().length < 5) return;
    try {
      await ref.read(apiProvider).reportError('offering', c.offeringId, message.trim());
      if (context.mounted) showMessage(context, 'Thank you. Our team will check this.');
    } catch (e) {
      if (context.mounted) showMessage(context, e.toString());
    }
  }
}

class _SaveButton extends ConsumerWidget {
  const _SaveButton(this.offeringId);
  final String offeringId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final list = ref.watch(shortlistProvider).value ?? const [];
    final saved = list.any((c) => c.offeringId == offeringId);
    return IconButton(
      tooltip: saved ? 'Remove from shortlist' : 'Save to shortlist',
      icon: Icon(saved ? Icons.bookmark : Icons.bookmark_border),
      onPressed: () async {
        try {
          await ref.read(shortlistProvider.notifier).toggle(offeringId);
          if (context.mounted) showMessage(context, saved ? 'Removed from shortlist' : 'Saved to shortlist');
        } catch (e) {
          if (context.mounted) showMessage(context, e.toString());
        }
      },
    );
  }
}

class _EligibilityCard extends StatelessWidget {
  const _EligibilityCard({required this.category, required this.outcomes,
      required this.nextSteps, this.ruleSetName, this.misses = const []});
  final String category;
  final String? ruleSetName;
  final List<RuleOutcome> outcomes;
  final List<String> nextSteps;
  final List<String> misses;

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context).textTheme;
    final colour = StatusChip.colour(context, category);
    return Card(
      shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12), side: BorderSide(color: colour, width: 1.5)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          StatusChip(category),
          if (ruleSetName != null)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text('Checked against: $ruleSetName', style: t.bodySmall),
            ),
          const SizedBox(height: 10),
          Text('Why', style: t.titleSmall),
          const SizedBox(height: 6),
          for (final o in outcomes)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                OutcomeIcon(o.outcome),
                const SizedBox(width: 8),
                Expanded(child: Text(o.message)),
              ]),
            ),
          if (nextSteps.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text('What to do next', style: t.titleSmall),
            const SizedBox(height: 4),
            for (final step in nextSteps)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Icon(Icons.arrow_right_alt, size: 20),
                  const SizedBox(width: 6),
                  Expanded(child: Text(step)),
                ]),
              ),
          ],
          if (misses.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text('Outside your preferences: ${misses.map(missLabel).join(', ')}', style: t.bodySmall),
          ],
        ]),
      ),
    );
  }
}

class _Row extends StatelessWidget {
  const _Row(this.label, this.value, {this.bold = false});
  final String label;
  final String value;
  final bool bold;

  @override
  Widget build(BuildContext context) {
    final style = bold ? const TextStyle(fontWeight: FontWeight.w700) : null;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Expanded(child: Text(label, style: style)),
        const SizedBox(width: 12),
        Flexible(child: Text(value, textAlign: TextAlign.end, style: style)),
      ]),
    );
  }
}

/// Plain-English description of a rule for the requirements list.
String? describeRule(Json rule, Reference r) {
  final p = rule['params'] as Json;
  String level(String? code) => switch (code) {
        'SSC' => 'Matric / O-Level',
        'DIPLOMA' => 'DAE',
        _ => 'Intermediate / A-Level',
      };
  List<String> strs(dynamic v) => (v as List? ?? const []).map((e) => e.toString()).toList();
  String orList(List<String> items) =>
      items.length <= 1 ? items.join() : '${items.sublist(0, items.length - 1).join(', ')} or ${items.last}';

  switch (rule['type']) {
    case 'accepted_qualification':
      final groups = strs(p['groups']).map(r.groupName).toList();
      final types = strs(p['types']).map((t) => r.types.where((x) => x.code == t).firstOrNull?.name ?? t).toList();
      if (groups.isNotEmpty) return 'Accepted backgrounds: ${orList(groups)}.';
      if (types.isNotEmpty) return 'Accepted qualifications: ${orList(types)}.';
      return 'Any ${level(p['level'])} background is accepted.';
    case 'required_subjects':
      final all = strs(p['all_of']).map(r.subjectName).toList();
      final parts = <String>[
        if (all.isNotEmpty) '${all.join(', ')} required',
        for (final g in (p['one_of'] as List? ?? const []))
          'one of ${orList(strs(g).map(r.subjectName).toList())}',
      ];
      return '${parts.join('; ')} in ${level(p['level'])}.';
    case 'min_percentage':
      return 'At least ${percent(p['min'] as num)} in ${level(p['level'])}.';
    case 'min_subject_marks':
      return 'At least ${percent(p['min_percentage'] as num)} in ${r.subjectName(p['subject'])}.';
    case 'entry_test_required':
      final tests = orList(strs(p['tests']).map(r.testName).toList());
      final min = p['min_score_percentage'];
      return 'Entry test: $tests${min != null ? ' (minimum ${percent(min as num)})' : ''}.';
    case 'gender':
      return 'Open to ${strs(p['allowed']).join(' and ')} students only.';
    case 'domicile':
      return '${titleCase(p['seat_type'] ?? 'Quota')} seats for domicile of '
          '${orList(strs(p['regions']).map(r.regionName).toList())}.';
    case 'max_age':
      return 'Maximum age ${p['years']} years on ${niceDate(p['on_date'])}.';
    case 'passing_year_window':
      return '${level(p['level'])} passed in ${p['min_year']} or later.';
    case 'result_status':
      return p['accept_part1'] == true ? 'You can apply with Part-I marks.' : null;
    case 'deficiency_allowed':
      return '${orList(strs(p['for_groups']).map(r.groupName).toList())} students can join with: ${p['course']}.';
    case 'ibcc_equivalence_required':
      return 'IBCC equivalence certificate required for A-Level / O-Level students.';
    case 'improved_result_policy':
      return p['accepted'] == true ? null : 'Improved (supplementary) results are not accepted.';
    case 'manual_note':
      return p['text'] as String?;
  }
  return null;
}
