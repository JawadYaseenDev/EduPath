import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../api.dart';
import '../state.dart';
import '../widgets.dart';
import 'offering_screen.dart';

final _reviewProvider = FutureProvider.autoDispose<Json>((ref) async {
  ref.watch(refreshProvider);
  return await ref.watch(apiProvider).get('/v1/admin/review') as Json;
});

/// Everything waiting for a second person (ADMIN_PANEL_PLAN § 3.9).
class ReviewScreen extends ConsumerWidget {
  const ReviewScreen({super.key});

  String _route(Json r) => switch (r['entity_type']) {
    'offering' => '/offerings/${r['entity_id']}',
    _ => '',
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final staff = ref.watch(sessionProvider).value;
    return PageScaffold(
      title: 'Review queue',
      child: AsyncBody(
        ref.watch(_reviewProvider),
        onRetry: () => ref.invalidate(_reviewProvider),
        builder: (d) {
          final records = (d['records'] as List).cast<Json>();
          final changes = (d['changes'] as List).cast<Json>();
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              if (!(staff?.canVerify ?? false))
                const Padding(
                  padding: EdgeInsets.only(bottom: 16),
                  child: Text('You can see this queue, but only data verifiers can approve.'),
                ),
              const Text('Rule: nobody can approve their own work. Check each item against its official source.'),
              const SizedBox(height: 16),
              Text('New records (${records.length})', style: Theme.of(context).textTheme.titleMedium),
              if (records.isEmpty) const Padding(padding: EdgeInsets.only(top: 8), child: Text('Nothing waiting.')),
              for (final r in records)
                Card(
                  margin: const EdgeInsets.only(top: 8),
                  child: ListTile(
                    leading: const Icon(Icons.fiber_new_outlined),
                    title: Text(r['label'] as String),
                    subtitle: Text(
                      '${titleCase(r['entity_type'])} · by ${r['edited_by_email'] ?? '-'} · ${shortDate(r['updated_at'])}',
                    ),
                    trailing: Wrap(
                      spacing: 8,
                      children: [
                        if (_route(r).isNotEmpty)
                          TextButton(onPressed: () => context.go(_route(r)), child: const Text('Open')),
                        if (staff?.canVerify ?? false) ...[
                          FilledButton(
                            onPressed: () => runAction(
                              context,
                              ref,
                              () => ref
                                  .read(apiProvider)
                                  .post('/v1/admin/records/${r['entity_type']}/${r['entity_id']}/approve'),
                            ),
                            child: const Text('Approve'),
                          ),
                          OutlinedButton(
                            onPressed: () async {
                              final note = await askText(context, 'Send back to draft', 'What needs fixing?');
                              if (note != null && context.mounted) {
                                await runAction(
                                  context,
                                  ref,
                                  () => ref.read(apiProvider).post(
                                    '/v1/admin/records/${r['entity_type']}/${r['entity_id']}/reject',
                                    {'note': note},
                                  ),
                                );
                              }
                            },
                            child: const Text('Reject'),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 24),
              Text('Changes to live data (${changes.length})', style: Theme.of(context).textTheme.titleMedium),
              if (changes.isEmpty) const Padding(padding: EdgeInsets.only(top: 8), child: Text('Nothing waiting.')),
              for (final c in changes) ChangeCard(change: c, showLink: true),
            ],
          );
        },
      ),
    );
  }
}
