import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../api.dart';
import '../state.dart';
import '../widgets.dart';

const _sectors = {'public': 'Public', 'private': 'Private', 'semi_government': 'Semi-government'};
const _genderPolicies = {'coeducation': 'Co-education', 'women_only': 'Women only', 'men_only': 'Men only'};

const universityFields = [
  FieldSpec('name', 'Full name', FieldKind.text, required: true),
  FieldSpec('short_name', 'Short name', FieldKind.text, help: 'e.g. UET, NUST'),
  FieldSpec('aliases', 'Other names people search for', FieldKind.list),
  FieldSpec('sector', 'Sector', FieldKind.choice, required: true, options: _sectors),
  FieldSpec('gender_policy', 'Admission policy', FieldKind.choice, options: _genderPolicies),
  FieldSpec('hec_recognised', 'HEC recognised', FieldKind.toggle),
  FieldSpec('website_url', 'Official website', FieldKind.text, help: 'https://...'),
  FieldSpec('admissions_url', 'Official admissions page', FieldKind.text, help: 'https://...'),
  FieldSpec('description', 'Short neutral description', FieldKind.multiline),
  FieldSpec('source_id', 'Source', FieldKind.source),
];

// ================================================================== list

final _universitiesProvider = FutureProvider.autoDispose.family<List<Json>, String>((ref, q) async {
  ref.watch(refreshProvider);
  return ((await ref.watch(apiProvider).get('/v1/admin/universities', {if (q.isNotEmpty) 'q': q})) as List)
      .cast<Json>();
});

class UniversitiesScreen extends ConsumerStatefulWidget {
  const UniversitiesScreen({super.key});
  @override
  ConsumerState<UniversitiesScreen> createState() => _UniversitiesScreenState();
}

class _UniversitiesScreenState extends ConsumerState<UniversitiesScreen> {
  String _q = '';

  @override
  Widget build(BuildContext context) {
    final staff = ref.watch(sessionProvider).value;
    final data = ref.watch(_universitiesProvider(_q));
    return PageScaffold(
      title: 'Universities',
      actions: [
        SizedBox(
          width: 280,
          child: TextField(
            decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: 'Search', isDense: true),
            onSubmitted: (v) => setState(() => _q = v.trim()),
          ),
        ),
        const SizedBox(width: 12),
        if (staff?.canEdit ?? false)
          FilledButton.icon(
            icon: const Icon(Icons.add),
            label: const Text('Add university'),
            onPressed: () async {
              final v = await showFormDialog(
                context,
                title: 'Add university',
                fields: universityFields,
                initial: {'sector': 'public', 'gender_policy': 'coeducation', 'hec_recognised': true},
              );
              if (v == null || !context.mounted) return;
              try {
                final r = await ref.read(apiProvider).post('/v1/admin/universities', v) as Json;
                ref.read(refreshProvider.notifier).bump();
                if (context.mounted) context.go('/universities/${r['id']}');
              } catch (e) {
                if (context.mounted) toast(context, e.toString(), error: true);
              }
            },
          ),
      ],
      child: AsyncBody(
        data,
        builder: (rows) => SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Card(
            child: SizedBox(
              width: double.infinity,
              child: DataTable(
                showCheckboxColumn: false,
                columns: const [
                  DataColumn(label: Text('University')),
                  DataColumn(label: Text('Sector')),
                  DataColumn(label: Text('Campuses'), numeric: true),
                  DataColumn(label: Text('Programmes'), numeric: true),
                  DataColumn(label: Text('Status')),
                  DataColumn(label: Text('Last verified')),
                ],
                rows: [
                  for (final u in rows)
                    DataRow(
                      onSelectChanged: (_) => context.go('/universities/${u['id']}'),
                      cells: [
                        DataCell(
                          Row(
                            children: [
                              Flexible(child: Text(u['name'] as String, overflow: TextOverflow.ellipsis)),
                              if (u['is_demo'] == true) ...[const SizedBox(width: 6), const Chip(label: Text('Demo'))],
                              if ((u['pending_changes'] as int) > 0) ...[
                                const SizedBox(width: 6),
                                Tooltip(
                                  message: 'Changes waiting for review',
                                  child: Icon(
                                    Icons.hourglass_top,
                                    size: 18,
                                    color: Theme.of(context).colorScheme.tertiary,
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),
                        DataCell(Text(_sectors[u['sector']] ?? '-')),
                        DataCell(Text('${u['campus_count']}')),
                        DataCell(Text('${u['programme_count']}')),
                        DataCell(StatusBadge(u['status'] as String)),
                        DataCell(Text(shortDate(u['verified_at']).split(' ').first)),
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
}

// ================================================================== detail

final _universityProvider = FutureProvider.autoDispose.family<Json, String>((ref, id) async {
  ref.watch(refreshProvider);
  return await ref.watch(apiProvider).get('/v1/admin/universities/$id') as Json;
});

class UniversityScreen extends ConsumerWidget {
  const UniversityScreen({super.key, required this.id});
  final String id;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(_universityProvider(id));
    final staff = ref.watch(sessionProvider).value;
    final reference = ref.watch(referenceProvider).value;
    final api = ref.read(apiProvider);
    return AsyncBody(
      data,
      builder: (u) {
        final campuses = (u['campuses'] as List).cast<Json>();
        return PageScaffold(
          title: u['name'] as String,
          breadcrumb: TextButton.icon(
            onPressed: () => context.go('/universities'),
            icon: const Icon(Icons.arrow_back, size: 16),
            label: const Text('Universities'),
          ),
          actions: [
            if (staff?.canEdit ?? false)
              OutlinedButton.icon(
                icon: const Icon(Icons.edit),
                label: const Text('Edit details'),
                onPressed: () async {
                  final v = await showFormDialog(
                    context,
                    title: 'Edit university',
                    fields: universityFields,
                    initial: u,
                  );
                  if (v != null && context.mounted) {
                    await runAction(
                      context,
                      ref,
                      () => api.put('/v1/admin/universities/$id', _pick(v, universityFields)),
                    );
                  }
                },
              ),
          ],
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              if (u['is_demo'] == true)
                const Padding(
                  padding: EdgeInsets.only(bottom: 12),
                  child: Text(
                    'This is fictional demo data used for testing.',
                    style: TextStyle(fontStyle: FontStyle.italic),
                  ),
                ),
              WorkflowActions(entityType: 'university', entityId: id, status: u['status'] as String),
              if (u['review_note'] != null) _ReviewNote(u['review_note'] as String),
              PendingChangesNote((u['pending_changes'] as List).length),
              const SizedBox(height: 12),
              Wrap(
                spacing: 24,
                runSpacing: 8,
                children: [
                  _Fact('Sector', _sectors[u['sector']] ?? '-'),
                  _Fact('Admission policy', _genderPolicies[u['gender_policy']] ?? '-'),
                  _Fact('HEC recognised', u['hec_recognised'] == true ? 'Yes' : 'No'),
                  _Fact('Website', u['website_url'] ?? '-'),
                  _Fact('Admissions page', u['admissions_url'] ?? '-'),
                  _Fact('Last verified', shortDate(u['verified_at'])),
                ],
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(child: Text('Campuses', style: Theme.of(context).textTheme.titleLarge)),
                  if (staff?.canEdit ?? false)
                    OutlinedButton.icon(
                      icon: const Icon(Icons.add),
                      label: const Text('Add campus'),
                      onPressed: () async {
                        final v = await showFormDialog(
                          context,
                          title: 'Add campus',
                          fields: _campusFields(reference),
                          initial: {'source_id': u['source_id']},
                        );
                        if (v != null && context.mounted) {
                          await runAction(
                            context,
                            ref,
                            () => api.post('/v1/admin/campuses', {...v, 'university_id': id}),
                            success: 'Campus added as draft',
                          );
                        }
                      },
                    ),
                ],
              ),
              const SizedBox(height: 8),
              if (campuses.isEmpty) const Text('No campuses yet.'),
              for (final c in campuses) _CampusCard(c, reference: reference),
            ],
          ),
        );
      },
    );
  }
}

Json _pick(Json values, List<FieldSpec> fields) => {for (final f in fields) f.key: values[f.key]};

List<FieldSpec> _campusFields(Json? reference) => [
  const FieldSpec('name', 'Campus name', FieldKind.text, required: true, help: 'e.g. Main Campus, Lahore Campus'),
  FieldSpec(
    'city_id',
    'City',
    FieldKind.choice,
    required: true,
    options: {
      for (final c in ((reference?['cities'] as List?) ?? const []).cast<Json>())
        c['id'] as String: '${c['name']} (${c['region_code']})',
    },
  ),
  const FieldSpec('is_main_campus', 'Main campus', FieldKind.toggle),
  const FieldSpec('address', 'Address', FieldKind.text),
  const FieldSpec(
    'gender_policy',
    'Campus admission policy (if different)',
    FieldKind.choice,
    options: _genderPolicies,
  ),
  const FieldSpec('latitude', 'Latitude', FieldKind.decimal),
  const FieldSpec('longitude', 'Longitude', FieldKind.decimal),
  const FieldSpec('source_id', 'Source', FieldKind.source),
];

const _hostelFields = [
  FieldSpec('for_gender', 'For', FieldKind.choice, required: true, options: {'female': 'Girls', 'male': 'Boys'}),
  FieldSpec(
    'location',
    'Location',
    FieldKind.choice,
    required: true,
    options: {
      'on_campus': 'On campus',
      'off_campus_university_managed': 'Off campus (university managed)',
      'affiliated_private': 'Private (affiliated)',
    },
  ),
  FieldSpec(
    'availability',
    'Availability',
    FieldKind.choice,
    required: true,
    options: {
      'available': 'Available',
      'limited': 'Limited seats',
      'not_available': 'Not available',
      'unknown': 'Unknown',
    },
  ),
  FieldSpec('fee_per_semester_pkr', 'Fee per semester (PKR)', FieldKind.integer),
  FieldSpec('notes', 'Notes', FieldKind.multiline),
  FieldSpec('source_id', 'Source', FieldKind.source),
];

List<FieldSpec> _programmeFields(Json? reference) {
  final fields = {for (final f in ((reference?['fields'] as List?) ?? const []).cast<Json>()) f['code']: f['name']};
  return [
    FieldSpec(
      'discipline_code',
      'Discipline',
      FieldKind.choice,
      required: true,
      options: {
        for (final d in ((reference?['disciplines'] as List?) ?? const []).cast<Json>())
          d['code'] as String: '${d['name']} (${fields[d['field_code']]})',
      },
    ),
    const FieldSpec(
      'title',
      'Title as written by the university',
      FieldKind.text,
      required: true,
      help: 'e.g. BS (Artificial Intelligence)',
    ),
    const FieldSpec(
      'degree_type',
      'Degree type',
      FieldKind.text,
      required: true,
      help: 'e.g. BS, BE, BSc Eng Tech, MBBS',
    ),
    const FieldSpec('duration_years', 'Duration (years)', FieldKind.decimal, required: true),
    const FieldSpec(
      'total_credit_hours',
      'Total credit hours',
      FieldKind.integer,
      help: 'Needed when fees are per credit hour',
    ),
    const FieldSpec(
      'shift',
      'Shift',
      FieldKind.choice,
      options: {'morning': 'Morning', 'evening': 'Evening', 'weekend': 'Weekend'},
    ),
    const FieldSpec('accreditation_body', 'Accreditation body', FieldKind.text, help: 'e.g. PEC, PMDC, NCEAC, NBEAC'),
    const FieldSpec(
      'accreditation_status',
      'Accreditation status',
      FieldKind.choice,
      options: {
        'accredited': 'Accredited',
        'provisional': 'Provisional',
        'not_accredited': 'Not accredited',
        'unknown': 'Unknown',
      },
    ),
    const FieldSpec('programme_url', 'Programme page', FieldKind.text, help: 'https://...'),
    const FieldSpec('source_id', 'Source', FieldKind.source),
  ];
}

class _CampusCard extends ConsumerWidget {
  const _CampusCard(this.c, {required this.reference});
  final Json c;
  final Json? reference;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final staff = ref.watch(sessionProvider).value;
    final canEdit = staff?.canEdit ?? false;
    final api = ref.read(apiProvider);
    final hostels = (c['hostels'] as List).cast<Json>();
    final programmes = (c['programmes'] as List).cast<Json>();
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
                  child: Text('${c['name']} · ${c['city_name']}', style: Theme.of(context).textTheme.titleMedium),
                ),
                if (canEdit)
                  IconButton(
                    tooltip: 'Edit campus',
                    icon: const Icon(Icons.edit_outlined),
                    onPressed: () async {
                      final fields = _campusFields(reference);
                      final v = await showFormDialog(context, title: 'Edit campus', fields: fields, initial: c);
                      if (v != null && context.mounted) {
                        await runAction(context, ref, () => api.put('/v1/admin/campuses/${c['id']}', _pick(v, fields)));
                      }
                    },
                  ),
              ],
            ),
            WorkflowActions(entityType: 'campus', entityId: c['id'] as String, status: c['status'] as String),
            if (c['review_note'] != null) _ReviewNote(c['review_note'] as String),
            PendingChangesNote((c['pending_changes'] as List).length),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(child: Text('Hostels', style: Theme.of(context).textTheme.titleSmall)),
                if (canEdit)
                  TextButton.icon(
                    icon: const Icon(Icons.add, size: 18),
                    label: const Text('Add hostel'),
                    onPressed: () async {
                      final v = await showFormDialog(
                        context,
                        title: 'Add hostel',
                        fields: _hostelFields,
                        initial: {'availability': 'available', 'location': 'on_campus', 'source_id': c['source_id']},
                      );
                      if (v != null && context.mounted) {
                        await runAction(
                          context,
                          ref,
                          () => api.post('/v1/admin/hostels', {...v, 'campus_id': c['id']}),
                          success: 'Hostel added as draft',
                        );
                      }
                    },
                  ),
              ],
            ),
            if (hostels.isEmpty) const Text('No hostel information.'),
            for (final h in hostels)
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.hotel_outlined),
                title: Text(
                  '${h['for_gender'] == 'female' ? 'Girls' : 'Boys'} · ${titleCase(h['location'])} · '
                  '${titleCase(h['availability'])}'
                  '${h['fee_per_semester_pkr'] != null ? ' · PKR ${h['fee_per_semester_pkr']}/sem' : ''}',
                ),
                subtitle: Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: WorkflowActions(
                    entityType: 'hostel',
                    entityId: h['id'] as String,
                    status: h['status'] as String,
                  ),
                ),
                trailing: canEdit
                    ? IconButton(
                        tooltip: 'Edit hostel',
                        icon: const Icon(Icons.edit_outlined),
                        onPressed: () async {
                          final v = await showFormDialog(
                            context,
                            title: 'Edit hostel',
                            fields: _hostelFields,
                            initial: h,
                          );
                          if (v != null && context.mounted) {
                            await runAction(
                              context,
                              ref,
                              () => api.put('/v1/admin/hostels/${h['id']}', _pick(v, _hostelFields)),
                            );
                          }
                        },
                      )
                    : null,
              ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(child: Text('Programmes', style: Theme.of(context).textTheme.titleSmall)),
                if (canEdit)
                  TextButton.icon(
                    icon: const Icon(Icons.add, size: 18),
                    label: const Text('Add programme'),
                    onPressed: () async {
                      final v = await showFormDialog(
                        context,
                        title: 'Add programme',
                        fields: _programmeFields(reference),
                        initial: {
                          'duration_years': 4,
                          'shift': 'morning',
                          'degree_type': 'BS',
                          'source_id': c['source_id'],
                        },
                      );
                      if (v != null && context.mounted) {
                        await runAction(
                          context,
                          ref,
                          () => api.post('/v1/admin/programmes', {...v, 'campus_id': c['id']}),
                          success: 'Programme added as draft',
                        );
                      }
                    },
                  ),
              ],
            ),
            if (programmes.isEmpty) const Text('No programmes yet.'),
            for (final p in programmes) _ProgrammeTile(p, reference: reference),
          ],
        ),
      ),
    );
  }
}

class _ProgrammeTile extends ConsumerWidget {
  const _ProgrammeTile(this.p, {required this.reference});
  final Json p;
  final Json? reference;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final staff = ref.watch(sessionProvider).value;
    final canEdit = staff?.canEdit ?? false;
    final api = ref.read(apiProvider);
    final offerings = (p['offerings'] as List).cast<Json>();
    final currentLabel = reference?['current_cycle']?['label'];
    final hasCurrent = offerings.any((o) => o['cycle_label'] == currentLabel);
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '${p['title']} · ${titleCase(p['shift'])} · ${p['duration_years']} years',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
              ),
              if (canEdit)
                IconButton(
                  tooltip: 'Edit programme',
                  icon: const Icon(Icons.edit_outlined),
                  onPressed: () async {
                    final fields = _programmeFields(reference);
                    final v = await showFormDialog(context, title: 'Edit programme', fields: fields, initial: p);
                    if (v != null && context.mounted) {
                      await runAction(context, ref, () => api.put('/v1/admin/programmes/${p['id']}', _pick(v, fields)));
                    }
                  },
                ),
            ],
          ),
          WorkflowActions(entityType: 'programme', entityId: p['id'] as String, status: p['status'] as String),
          if (p['review_note'] != null) _ReviewNote(p['review_note'] as String),
          PendingChangesNote((p['pending_changes'] as List).length),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              for (final o in offerings)
                ActionChip(
                  avatar: Icon(o['status'] == 'published' ? Icons.check_circle : Icons.edit_note, size: 18),
                  label: Text(
                    '${o['cycle_label']} · ${titleCase(o['status'])}'
                    '${(o['pending_changes'] as int) > 0 ? ' · ${o['pending_changes']} pending' : ''}',
                  ),
                  onPressed: () => context.go('/offerings/${o['id']}'),
                ),
              if (!hasCurrent && canEdit)
                OutlinedButton.icon(
                  icon: const Icon(Icons.add, size: 18),
                  label: Text('Start $currentLabel data'),
                  onPressed: () async {
                    try {
                      final r = await api.post('/v1/admin/offerings', {
                        'programme_id': p['id'],
                        'copy_from_previous': offerings.isNotEmpty,
                      }) as Json;
                      ref.read(refreshProvider.notifier).bump();
                      if (context.mounted) {
                        toast(
                          context,
                          offerings.isNotEmpty
                              ? 'Draft created from last year. Check every value against this year\'s prospectus.'
                              : 'Draft created.',
                        );
                        context.go('/offerings/${r['id']}');
                      }
                    } catch (e) {
                      if (context.mounted) toast(context, e.toString(), error: true);
                    }
                  },
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Fact extends StatelessWidget {
  const _Fact(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(label, style: Theme.of(context).textTheme.labelMedium),
      SelectableText(value),
    ],
  );
}

class _ReviewNote extends StatelessWidget {
  const _ReviewNote(this.note);
  final String note;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 8),
    child: Text('Reviewer note: $note', style: TextStyle(color: Theme.of(context).colorScheme.error)),
  );
}
