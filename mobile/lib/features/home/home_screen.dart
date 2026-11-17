import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../core/format.dart';
import '../../state/providers.dart';
import '../../widgets/common.dart';

/// Dashboard (PDF FR-01: students land here after login).
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(profileProvider);
    final recs = ref.watch(recommendationsProvider);
    final shortlist = ref.watch(shortlistProvider);
    final t = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(title: const Text('UniRah')),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(profileProvider);
          ref.invalidate(recommendationsProvider);
          ref.invalidate(shortlistProvider);
        },
        child: ListView(padding: const EdgeInsets.all(16), children: [
          ...profile.when(
            loading: () => [const Loading()],
            error: (e, _) => [ErrorView(e, onRetry: () => ref.invalidate(profileProvider))],
            data: (p) => [
              Text('Assalam-o-Alaikum${p.fullName == null ? '' : ', ${p.fullName!.split(' ').first}'}',
                  style: t.headlineSmall),
              const SizedBox(height: 16),
              if (p.completeness.percent < 100)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text('Your profile is ${p.completeness.percent}% complete', style: t.titleMedium),
                      const SizedBox(height: 8),
                      LinearProgressIndicator(value: p.completeness.percent / 100),
                      const SizedBox(height: 12),
                      FilledButton(
                          onPressed: () => context.go('/setup'),
                          child: const Text('Complete my profile')),
                    ]),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 12),
          recs.when(
            loading: () => const Card(child: SizedBox(height: 120, child: Loading())),
            error: (e, _) => ErrorView(e, onRetry: () => ref.invalidate(recommendationsProvider)),
            data: (run) {
              if (run == null) {
                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text('Find your options', style: t.titleMedium),
                      const SizedBox(height: 6),
                      const Text('When your profile is ready, we will check every programme '
                          'against its published requirements.'),
                      const SizedBox(height: 12),
                      FilledButton.icon(
                        icon: const Icon(Icons.search),
                        label: const Text('Find my universities'),
                        onPressed: () async {
                          await ref.read(recommendationsProvider.notifier).run();
                          final r = ref.read(recommendationsProvider);
                          if (!context.mounted) return;
                          r.hasError ? showMessage(context, r.error.toString()) : context.go('/results');
                        },
                      ),
                    ]),
                  ),
                );
              }
              final eligible = run.group('eligible').length;
              final potential = run.group('potentially_eligible').length;
              final notEligible = run.group('not_eligible', includeHidden: true).length;
              return Card(
                child: InkWell(
                  onTap: () => context.go('/results'),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Row(children: [
                        Expanded(child: Text('Your results', style: t.titleMedium)),
                        const Icon(Icons.chevron_right),
                      ]),
                      Text('Based on ${run.cycleLabel} data · checked ${niceDate(run.createdAt)}',
                          style: t.bodySmall),
                      const SizedBox(height: 12),
                      Wrap(spacing: 16, runSpacing: 8, children: [
                        _Count('eligible', eligible),
                        if (!run.strict) _Count('potentially_eligible', potential),
                        _Count('not_eligible', notEligible),
                      ]),
                      if (run.isOutdated) ...[
                        const SizedBox(height: 12),
                        const InfoBanner('Your profile changed. Update your results.',
                            icon: Icons.update),
                      ],
                    ]),
                  ),
                ),
              );
            },
          ),
          shortlist.maybeWhen(
            data: (items) {
              final dated = items.where((c) => c.applicationsClose != null).toList()
                ..sort((a, b) => a.applicationsClose!.compareTo(b.applicationsClose!));
              if (dated.isEmpty) return const SizedBox.shrink();
              return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const SectionTitle('Upcoming deadlines'),
                for (final c in dated.take(3))
                  Card(
                    margin: const EdgeInsets.only(bottom: 8),
                    child: ListTile(
                      leading: const Icon(Icons.event),
                      title: Text(c.programmeTitle),
                      subtitle: Text(c.universityName),
                      trailing: Text(niceDate(c.applicationsClose)),
                      onTap: () => context.push('/programme/${c.offeringId}'),
                    ),
                  ),
              ]);
            },
            orElse: () => const SizedBox.shrink(),
          ),
          const SectionTitle('Explore'),
          Card(
            child: ListTile(
              leading: const Icon(Icons.travel_explore),
              title: const Text('Search all universities and programmes'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.go('/explore'),
            ),
          ),
        ]),
      ),
    );
  }
}

class _Count extends StatelessWidget {
  const _Count(this.category, this.count);
  final String category;
  final int count;

  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
        Text('$count ', style: Theme.of(context).textTheme.titleLarge),
        StatusChip(category, dense: true),
      ]);
}
