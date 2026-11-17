// Login, dashboard, reports, audit log and settings.
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../api.dart';
import '../state.dart';
import '../widgets.dart';

// ================================================================== login

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(sessionProvider.notifier).signIn(_email.text.trim(), _password.text);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: Center(
      child: SizedBox(
        width: 400,
        child: Card(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: AutofillGroup(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Center(child: Image.asset('assets/logo.png', height: 72, semanticLabel: 'EduRecommend logo')),
                  const SizedBox(height: 8),
                  Text('EduRecommend Admin', textAlign: TextAlign.center, style: Theme.of(context).textTheme.headlineSmall),
                  const Text('Staff only', textAlign: TextAlign.center),
                  const SizedBox(height: 24),
                  TextField(
                    controller: _email,
                    autofillHints: const [AutofillHints.email],
                    onSubmitted: (_) => _submit(),
                    decoration: const InputDecoration(labelText: 'Email'),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _password,
                    obscureText: true,
                    autofillHints: const [AutofillHints.password],
                    decoration: const InputDecoration(labelText: 'Password'),
                    onSubmitted: (_) => _submit(),
                  ),
                  if (_error != null) ...[
                    const SizedBox(height: 12),
                    Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                  ],
                  const SizedBox(height: 20),
                  FilledButton(onPressed: _busy ? null : _submit, child: Text(_busy ? 'Signing in...' : 'Sign in')),
                ],
              ),
            ),
          ),
        ),
      ),
    ),
  );
}

// ================================================================== dashboard

final _dashboardProvider = FutureProvider.autoDispose<Json>((ref) async {
  ref.watch(refreshProvider);
  return await ref.watch(apiProvider).get('/v1/admin/dashboard') as Json;
});

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(_dashboardProvider);
    return PageScaffold(
      title: 'Dashboard',
      child: AsyncBody(
        data,
        onRetry: () => ref.invalidate(_dashboardProvider),
        builder: (d) {
          final counts = (d['counts'] as Json).cast<String, dynamic>();
          Widget tile(String label, Object value, IconData icon, {VoidCallback? onTap, bool warn = false}) => SizedBox(
            width: 240,
            child: Card(
              child: InkWell(
                onTap: onTap,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Icon(
                        icon,
                        size: 32,
                        color: warn ? Theme.of(context).colorScheme.error : Theme.of(context).colorScheme.primary,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('$value', style: Theme.of(context).textTheme.headlineMedium),
                            Text(label),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          );
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Text(
                'Current admission cycle: ${(d['cycle'] as Json)['label']}',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 16),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  tile(
                    'Waiting for review',
                    d['pending_reviews'],
                    Icons.rate_review,
                    onTap: () => context.go('/review'),
                    warn: (d['pending_reviews'] as int) > 0,
                  ),
                  tile(
                    'Open student reports',
                    d['open_reports'],
                    Icons.flag,
                    onTap: () => context.go('/reports'),
                    warn: (d['open_reports'] as int) > 0,
                  ),
                  tile(
                    'Programmes without ${(d['cycle'] as Json)['label']} data',
                    d['programmes_without_current_offering'],
                    Icons.history,
                    onTap: () => context.go('/universities'),
                    warn: (d['programmes_without_current_offering'] as int) > 0,
                  ),
                  tile('Students', d['students'], Icons.school),
                  tile('Recommendation runs', d['recommendation_runs'], Icons.insights),
                ],
              ),
              const SizedBox(height: 24),
              Text('Records by status', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              Card(
                child: DataTable(
                  columns: const [
                    DataColumn(label: Text('Type')),
                    DataColumn(label: Text('Published'), numeric: true),
                    DataColumn(label: Text('Waiting for review'), numeric: true),
                    DataColumn(label: Text('Draft'), numeric: true),
                    DataColumn(label: Text('Archived'), numeric: true),
                  ],
                  rows: [
                    for (final e in counts.entries)
                      DataRow(
                        cells: [
                          DataCell(Text(titleCase(e.key))),
                          for (final s in const ['published', 'pending_review', 'draft', 'archived'])
                            DataCell(Text('${(e.value as Map)[s] ?? 0}')),
                        ],
                      ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

// ================================================================== reports

final _reportsProvider = FutureProvider.autoDispose.family<List<Json>, String?>((ref, status) async {
  ref.watch(refreshProvider);
  return ((await ref.watch(apiProvider).get('/v1/admin/reports', {'status': ?status})) as List).cast<Json>();
});

class ReportsScreen extends ConsumerStatefulWidget {
  const ReportsScreen({super.key});
  @override
  ConsumerState<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends ConsumerState<ReportsScreen> {
  String? _status = 'new';

  @override
  Widget build(BuildContext context) {
    final data = ref.watch(_reportsProvider(_status));
    return PageScaffold(
      title: 'Student error reports',
      actions: [
        SegmentedButton<String?>(
          segments: const [
            ButtonSegment(value: 'new', label: Text('New')),
            ButtonSegment(value: 'in_review', label: Text('In review')),
            ButtonSegment(value: null, label: Text('All')),
          ],
          selected: {_status},
          onSelectionChanged: (s) => setState(() => _status = s.first),
        ),
      ],
      child: AsyncBody(
        data,
        builder: (rows) {
          if (rows.isEmpty) return const Center(child: Text('No reports here.'));
          return ListView.separated(
            padding: const EdgeInsets.all(24),
            itemCount: rows.length,
            separatorBuilder: (_, _) => const SizedBox(height: 8),
            itemBuilder: (context, i) {
              final r = rows[i];
              return Card(
                child: ListTile(
                  title: Text(r['message'] as String),
                  subtitle: Text('${r['label']} · ${titleCase(r['status'])} · ${shortDate(r['created_at'])}'),
                  trailing: PopupMenuButton<String>(
                    tooltip: 'Change status',
                    onSelected: (s) => runAction(
                      context,
                      ref,
                      () => ref.read(apiProvider).put('/v1/admin/reports/${r['id']}', {'status': s}),
                      success: 'Report marked ${titleCase(s).toLowerCase()}',
                    ),
                    itemBuilder: (_) => const [
                      PopupMenuItem(value: 'in_review', child: Text('Mark in review')),
                      PopupMenuItem(value: 'fixed', child: Text('Mark fixed')),
                      PopupMenuItem(value: 'rejected', child: Text('Reject (information was correct)')),
                    ],
                  ),
                  onTap: r['entity_type'] == 'offering' ? () => context.go('/offerings/${r['entity_id']}') : null,
                ),
              );
            },
          );
        },
      ),
    );
  }
}

// ================================================================== audit

final _auditProvider = FutureProvider.autoDispose<List<Json>>((ref) async {
  ref.watch(refreshProvider);
  return ((await ref.watch(apiProvider).get('/v1/admin/audit', {'limit': 200})) as List).cast<Json>();
});

class AuditScreen extends ConsumerWidget {
  const AuditScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) => PageScaffold(
    title: 'Change history',
    child: AsyncBody(
      ref.watch(_auditProvider),
      builder: (rows) => SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Card(
          child: SizedBox(
            width: double.infinity,
            child: DataTable(
              columns: const [
                DataColumn(label: Text('When')),
                DataColumn(label: Text('Who')),
                DataColumn(label: Text('Action')),
                DataColumn(label: Text('Record')),
              ],
              rows: [
                for (final r in rows)
                  DataRow(
                    cells: [
                      DataCell(Text(shortDate(r['at']))),
                      DataCell(Text('${r['actor'] ?? '-'}')),
                      DataCell(Text(titleCase(r['action']))),
                      DataCell(
                        Text('${titleCase(r['entity_type'])} ${((r['entity_id'] as String?) ?? '').split('-').first}'),
                      ),
                    ],
                  ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}

// ================================================================== settings

final _settingsProvider = FutureProvider.autoDispose<(Json, List<Json>, List<Json>)>((ref) async {
  ref.watch(refreshProvider);
  final api = ref.watch(apiProvider);
  final mode = await api.get('/v1/admin/settings/result-mode') as Json;
  final cycles = ((await api.get('/v1/admin/cycles')) as List).cast<Json>();
  final staff = ((await api.get('/v1/admin/staff')) as List).cast<Json>();
  return (mode, cycles, staff);
});

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final api = ref.read(apiProvider);
    final me = ref.watch(sessionProvider).value;
    return PageScaffold(
      title: 'Settings',
      child: AsyncBody(
        ref.watch(_settingsProvider),
        builder: (data) {
          final (mode, cycles, staff) = data;
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Text('Result display mode', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 4),
              const Text(
                '"Strict PDF" follows the original workflow exactly: only Eligible options are '
                'recommended. "Extended" also shows Potentially Eligible options in their own group '
                '(needs supervisor approval - see docs/CHANGE_REQUEST_FOR_SUPERVISOR.md).',
              ),
              const SizedBox(height: 8),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: 'extended', label: Text('Extended')),
                  ButtonSegment(value: 'strict_pdf', label: Text('Strict PDF')),
                ],
                selected: {mode['mode'] as String},
                onSelectionChanged: (s) => runAction(
                  context,
                  ref,
                  () => api.put('/v1/admin/settings/result-mode', {'mode': s.first}),
                  success: 'Result mode updated',
                ),
              ),
              const SizedBox(height: 32),
              Row(
                children: [
                  Expanded(child: Text('Admission cycles', style: Theme.of(context).textTheme.titleMedium)),
                  OutlinedButton.icon(
                    icon: const Icon(Icons.add),
                    label: const Text('New cycle'),
                    onPressed: () async {
                      final v = await showFormDialog(
                        context,
                        title: 'New admission cycle',
                        fields: const [
                          FieldSpec('year', 'Year', FieldKind.integer, required: true),
                          FieldSpec('label', 'Label', FieldKind.text, required: true, help: 'e.g. Fall 2028'),
                        ],
                      );
                      if (v != null && context.mounted) {
                        await runAction(context, ref, () => api.post('/v1/admin/cycles', v), success: 'Cycle created');
                      }
                    },
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Card(
                child: Column(
                  children: [
                    for (final c in cycles)
                      ListTile(
                        title: Text(c['label'] as String),
                        subtitle: Text('${c['year']}'),
                        trailing: c['is_current'] == true
                            ? const Chip(label: Text('Current'))
                            : TextButton(
                                onPressed: () async {
                                  if (await confirm(
                                        context,
                                        'Make ${c['label']} the current cycle?',
                                        'Students will see "previous cycle" warnings on programmes that have no '
                                            '${c['label']} data yet.',
                                      ) &&
                                      context.mounted) {
                                    await runAction(
                                      context,
                                      ref,
                                      () => api.put('/v1/admin/cycles/${c['id']}/current', {}),
                                      success: '${c['label']} is now current',
                                    );
                                  }
                                },
                                child: const Text('Make current'),
                              ),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 32),
              Row(
                children: [
                  Expanded(child: Text('Staff accounts', style: Theme.of(context).textTheme.titleMedium)),
                  OutlinedButton.icon(
                    icon: const Icon(Icons.person_add),
                    label: const Text('Add staff'),
                    onPressed: () async {
                      final v = await showFormDialog(
                        context,
                        title: 'Add staff account',
                        fields: const [
                          FieldSpec('email', 'Email', FieldKind.text, required: true),
                          FieldSpec(
                            'password',
                            'Temporary password',
                            FieldKind.text,
                            required: true,
                            help: 'At least 8 characters. Share it privately.',
                          ),
                          FieldSpec(
                            'role',
                            'Role',
                            FieldKind.choice,
                            required: true,
                            options: {
                              'data_editor': 'Data editor - enters data',
                              'data_verifier': 'Data verifier - reviews and publishes',
                              'support': 'Support - handles student reports',
                              'super_admin': 'Super admin - everything',
                            },
                          ),
                        ],
                      );
                      if (v != null && context.mounted) {
                        await runAction(
                          context,
                          ref,
                          () => api.post('/v1/admin/staff', v),
                          success: 'Staff account created',
                        );
                      }
                    },
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Card(
                child: Column(
                  children: [
                    for (final s in staff)
                      ListTile(
                        leading: const Icon(Icons.badge_outlined),
                        title: Text(s['email'] as String),
                        subtitle: Text(titleCase(s['role'] as String)),
                        trailing: s['id'] == me?.id
                            ? const Text('You')
                            : PopupMenuButton<String>(
                                tooltip: 'Change role',
                                onSelected: (role) => runAction(
                                  context,
                                  ref,
                                  () => api.put('/v1/admin/users/${s['id']}/role', {'role': role}),
                                  success: 'Role updated',
                                ),
                                itemBuilder: (_) => [
                                  for (final r in const [
                                    'data_editor',
                                    'data_verifier',
                                    'support',
                                    'super_admin',
                                    'student',
                                  ])
                                    PopupMenuItem(
                                      value: r,
                                      child: Text(r == 'student' ? 'Remove staff access' : titleCase(r)),
                                    ),
                                ],
                              ),
                      ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
