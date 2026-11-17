import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../core/format.dart';
import '../../data/models.dart';
import '../../state/providers.dart';
import '../../widgets/common.dart';

/// Saved options (FR-06) with compare (FR-05).
class ShortlistScreen extends ConsumerStatefulWidget {
  const ShortlistScreen({super.key});

  @override
  ConsumerState<ShortlistScreen> createState() => _ShortlistScreenState();
}

class _ShortlistScreenState extends ConsumerState<ShortlistScreen> {
  final Set<String> _compare = {};

  @override
  Widget build(BuildContext context) {
    final list = ref.watch(shortlistProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Shortlist')),
      floatingActionButton: _compare.length >= 2
          ? FloatingActionButton.extended(
              onPressed: () => context.push('/compare', extra: _compare.toList()),
              icon: const Icon(Icons.compare_arrows),
              label: Text('Compare ${_compare.length}'),
            )
          : null,
      body: list.when(
        loading: () => const Loading(),
        error: (e, _) => ErrorView(e, onRetry: () => ref.invalidate(shortlistProvider)),
        data: (items) {
          if (items.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  const Icon(Icons.bookmark_border, size: 48),
                  const SizedBox(height: 12),
                  const Text('No saved programmes yet. Tap the bookmark on a programme to save it.',
                      textAlign: TextAlign.center),
                  const SizedBox(height: 12),
                  OutlinedButton(onPressed: () => context.go('/explore'), child: const Text('Explore')),
                ]),
              ),
            );
          }
          return ListView(padding: const EdgeInsets.all(16), children: [
            Text('Select 2 or 3 to compare.', style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 8),
            for (final c in items)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: OfferingTile(
                  c,
                  category: c.category,
                  onTap: () => context.push('/programme/${c.offeringId}'),
                  trailing: Checkbox(
                    value: _compare.contains(c.offeringId),
                    onChanged: (on) => setState(() {
                      if (on == true && _compare.length < 3) {
                        _compare.add(c.offeringId);
                      } else if (on == true) {
                        showMessage(context, 'You can compare up to 3 programmes.');
                      } else {
                        _compare.remove(c.offeringId);
                      }
                    }),
                  ),
                  footer: Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Row(children: [
                      if (c.applicationsClose != null)
                        Expanded(
                          child: Text('Applications close ${niceDate(c.applicationsClose)}',
                              style: Theme.of(context).textTheme.bodySmall),
                        )
                      else
                        const Spacer(),
                      TextButton(
                        onPressed: () async {
                          final detail = await ref.read(offeringProvider(c.offeringId).future);
                          if (context.mounted) {
                            openLink(context, detail.admissionsUrl ?? detail.websiteUrl);
                          }
                        },
                        child: const Text('Official page'),
                      ),
                      IconButton(
                        tooltip: 'Remove',
                        icon: const Icon(Icons.delete_outline),
                        onPressed: () {
                          _compare.remove(c.offeringId);
                          ref.read(shortlistProvider.notifier).toggle(c.offeringId);
                        },
                      ),
                    ]),
                  ),
                ),
              ),
          ]);
        },
      ),
    );
  }
}

class CompareScreen extends ConsumerWidget {
  const CompareScreen({super.key, required this.offeringIds});
  final List<String> offeringIds;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final details = [for (final id in offeringIds) ref.watch(offeringProvider(id))];
    final shortlist = ref.watch(shortlistProvider).value ?? const <OfferingCard>[];
    return Scaffold(
      appBar: AppBar(title: const Text('Compare')),
      body: () {
        if (details.any((d) => d.isLoading)) return const Loading();
        final error = details.where((d) => d.hasError).firstOrNull;
        if (error != null) return ErrorView(error.error!);
        final items = details.map((d) => d.value!).toList();
        String? category(String id) =>
            shortlist.where((c) => c.offeringId == id).firstOrNull?.category;

        final rows = <(String, List<Widget>)>[
          ('Status', [
            for (final d in items)
              category(d.card.offeringId) == null
                  ? const Text('Not checked')
                  : StatusChip(category(d.card.offeringId)!, dense: true)
          ]),
          ('University', [for (final d in items) Text(d.card.universityName)]),
          ('Location', [for (final d in items) Text('${d.card.campusName}, ${d.card.city}')]),
          ('Type', [for (final d in items) Text(sectorLabel(d.card.sector))]),
          ('Duration', [for (final d in items) Text('${d.card.durationYears.toStringAsFixed(0)} years')]),
          ('Per semester', [for (final d in items) Text(pkr(d.card.chargesPerSemester))]),
          ('First year total', [for (final d in items) Text(pkr(d.card.firstYearTotal))]),
          ('Hostel', [
            for (final d in items)
              Text(d.hostels.isEmpty
                  ? 'No information'
                  : d.hostels
                      .map((h) => '${h.forGender == 'female' ? 'Girls' : 'Boys'}: ${titleCase(h.availability)}')
                      .join('\n'))
          ]),
          ('Entry test', [for (final d in items) Text(d.card.entryTests.isEmpty ? 'None listed' : d.card.entryTests.join(', '))]),
          ('Accreditation', [
            for (final d in items)
              Text(d.card.accreditationBody == null
                  ? '-'
                  : '${d.card.accreditationBody}: ${titleCase(d.card.accreditationStatus ?? 'unknown')}')
          ]),
          ('Applications close', [for (final d in items) Text(niceDate(d.card.applicationsClose))]),
        ];

        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Table(
              defaultVerticalAlignment: TableCellVerticalAlignment.top,
              columnWidths: const {0: FixedColumnWidth(110)},
              border: TableBorder(
                  horizontalInside: BorderSide(color: Theme.of(context).colorScheme.outlineVariant)),
              children: [
                TableRow(children: [
                  const SizedBox(),
                  for (final d in items)
                    Padding(
                      padding: const EdgeInsets.all(8),
                      child: Text(d.card.programmeTitle,
                          style: Theme.of(context).textTheme.titleSmall),
                    ),
                ]),
                for (final (label, cells) in rows)
                  TableRow(children: [
                    Padding(
                      padding: const EdgeInsets.all(8),
                      child: Text(label, style: Theme.of(context).textTheme.labelLarge),
                    ),
                    for (final cell in cells) Padding(padding: const EdgeInsets.all(8), child: cell),
                  ]),
              ],
            ),
            const SizedBox(height: 16),
            const NoGuaranteeNote(),
          ]),
        );
      }(),
    );
  }
}
