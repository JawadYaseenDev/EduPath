import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import 'api.dart';
import 'state.dart';

// ------------------------------------------------------------------ helpers

void toast(BuildContext context, String message, {bool error = false}) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: error ? Theme.of(context).colorScheme.error : null,
        behavior: SnackBarBehavior.floating,
        width: 520,
      ),
    );
}

/// Runs an API action, shows its message (or error), and refreshes screens.
Future<bool> runAction(
  BuildContext context,
  WidgetRef ref,
  Future<dynamic> Function() action, {
  String? success,
}) async {
  try {
    final result = await action();
    final msg = success ?? (result is Map && result['message'] is String ? result['message'] as String : 'Saved');
    if (context.mounted) toast(context, msg);
    ref.read(refreshProvider.notifier).bump();
    return true;
  } catch (e) {
    if (context.mounted) toast(context, e.toString(), error: true);
    return false;
  }
}

String titleCase(String? code) =>
    (code ?? '-').split('_').where((p) => p.isNotEmpty).map((p) => p[0].toUpperCase() + p.substring(1)).join(' ');

String shortDate(String? iso) {
  if (iso == null) return '-';
  final d = DateTime.tryParse(iso)?.toLocal();
  if (d == null) return iso;
  String two(int n) => n.toString().padLeft(2, '0');
  return '${d.year}-${two(d.month)}-${two(d.day)} ${two(d.hour)}:${two(d.minute)}';
}

// ------------------------------------------------------------------ status

class StatusBadge extends StatelessWidget {
  const StatusBadge(this.status, {super.key});
  final String status;

  @override
  Widget build(BuildContext context) {
    final s = Theme.of(context).colorScheme;
    final (bg, fg, label) = switch (status) {
      'published' => (s.primaryContainer, s.onPrimaryContainer, 'Published'),
      'pending_review' => (s.tertiaryContainer, s.onTertiaryContainer, 'Waiting for review'),
      'archived' => (s.surfaceContainerHighest, s.onSurfaceVariant, 'Archived'),
      _ => (s.secondaryContainer, s.onSecondaryContainer, 'Draft'),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(6)),
      child: Text(label, style: Theme.of(context).textTheme.labelMedium?.copyWith(color: fg)),
    );
  }
}

/// Submit / approve / reject / archive buttons for one record (ADMIN_PANEL_PLAN § 3.9).
class WorkflowActions extends ConsumerWidget {
  const WorkflowActions({super.key, required this.entityType, required this.entityId, required this.status});
  final String entityType;
  final String entityId;
  final String status;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final staff = ref.watch(sessionProvider).value;
    if (staff == null) return const SizedBox.shrink();
    final api = ref.read(apiProvider);
    final base = '/v1/admin/records/$entityType/$entityId';
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        StatusBadge(status),
        if (status == 'draft' && staff.canEdit)
          FilledButton.tonalIcon(
            icon: const Icon(Icons.send, size: 18),
            label: const Text('Submit for review'),
            onPressed: () => runAction(context, ref, () => api.post('$base/submit')),
          ),
        if (status == 'pending_review' && staff.canVerify) ...[
          FilledButton.icon(
            icon: const Icon(Icons.verified, size: 18),
            label: const Text('Approve & publish'),
            onPressed: () => runAction(context, ref, () => api.post('$base/approve')),
          ),
          OutlinedButton(
            onPressed: () async {
              final note = await askText(context, 'Send back to draft', 'What needs fixing?');
              if (note != null && context.mounted) {
                await runAction(context, ref, () => api.post('$base/reject', {'note': note}));
              }
            },
            child: const Text('Reject'),
          ),
        ],
        if (status != 'archived' && staff.canEdit)
          TextButton(
            onPressed: () async {
              if (await confirm(
                    context,
                    'Archive this record?',
                    'It will no longer be shown to students. You can restore it later.',
                  ) &&
                  context.mounted) {
                await runAction(context, ref, () => api.post('$base/archive'));
              }
            },
            child: const Text('Archive'),
          ),
        if (status == 'archived' && staff.canEdit)
          TextButton(
            onPressed: () => runAction(context, ref, () => api.post('$base/restore')),
            child: const Text('Restore'),
          ),
      ],
    );
  }
}

class PendingChangesNote extends StatelessWidget {
  const PendingChangesNote(this.count, {super.key});
  final int count;

  @override
  Widget build(BuildContext context) {
    if (count == 0) return const SizedBox.shrink();
    final s = Theme.of(context).colorScheme;
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(color: s.tertiaryContainer, borderRadius: BorderRadius.circular(8)),
      child: Row(
        children: [
          Icon(Icons.hourglass_top, size: 18, color: s.onTertiaryContainer),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              '$count change${count == 1 ? '' : 's'} waiting for review. Students see the '
              'published version until a verifier approves.',
              style: TextStyle(color: s.onTertiaryContainer),
            ),
          ),
        ],
      ),
    );
  }
}

// ------------------------------------------------------------------ dialogs

Future<bool> confirm(BuildContext context, String title, String body) async =>
    await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text(title),
        content: Text(body),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(c, true), child: const Text('Continue')),
        ],
      ),
    ) ??
    false;

Future<String?> askText(BuildContext context, String title, String hint) async {
  final controller = TextEditingController();
  final result = await showDialog<String>(
    context: context,
    builder: (c) => AlertDialog(
      title: Text(title),
      content: SizedBox(
        width: 420,
        child: TextField(
          controller: controller,
          maxLines: 3,
          decoration: InputDecoration(hintText: hint),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(c), child: const Text('Cancel')),
        FilledButton(onPressed: () => Navigator.pop(c, controller.text.trim()), child: const Text('OK')),
      ],
    ),
  );
  controller.dispose();
  return (result == null || result.length < 3) ? null : result;
}

// ------------------------------------------------------------------ generic form

enum FieldKind { text, multiline, integer, decimal, toggle, choice, list, source }

class FieldSpec {
  const FieldSpec(this.key, this.label, this.kind, {this.options = const {}, this.required = false, this.help});
  final String key;
  final String label;
  final FieldKind kind;
  final Map<String, String> options; // value -> label, for FieldKind.choice
  final bool required;
  final String? help;
}

/// Opens a form dialog. Returns the edited values, or null if cancelled.
Future<Json?> showFormDialog(
  BuildContext context, {
  required String title,
  required List<FieldSpec> fields,
  Json initial = const {},
}) {
  return showDialog<Json>(
    context: context,
    builder: (_) => _FormDialog(title: title, fields: fields, initial: initial),
  );
}

class _FormDialog extends ConsumerStatefulWidget {
  const _FormDialog({required this.title, required this.fields, required this.initial});
  final String title;
  final List<FieldSpec> fields;
  final Json initial;

  @override
  ConsumerState<_FormDialog> createState() => _FormDialogState();
}

class _FormDialogState extends ConsumerState<_FormDialog> {
  final _form = GlobalKey<FormState>();
  late final Json _values = {...widget.initial};
  final Map<String, TextEditingController> _text = {};

  @override
  void initState() {
    super.initState();
    for (final f in widget.fields) {
      if (const [
        FieldKind.text,
        FieldKind.multiline,
        FieldKind.integer,
        FieldKind.decimal,
        FieldKind.list,
      ].contains(f.kind)) {
        final v = widget.initial[f.key];
        _text[f.key] = TextEditingController(text: v == null ? '' : (v is List ? v.join(', ') : v.toString()));
      }
    }
  }

  @override
  void dispose() {
    for (final c in _text.values) {
      c.dispose();
    }
    super.dispose();
  }

  void _save() {
    if (!_form.currentState!.validate()) return;
    for (final f in widget.fields) {
      final c = _text[f.key];
      if (c == null) continue;
      final t = c.text.trim();
      _values[f.key] = switch (f.kind) {
        FieldKind.integer => t.isEmpty ? null : int.parse(t),
        FieldKind.decimal => t.isEmpty ? null : double.parse(t),
        FieldKind.list =>
          t.isEmpty ? <String>[] : t.split(',').map((e) => e.trim()).where((e) => e.isNotEmpty).toList(),
        _ => t.isEmpty ? null : t,
      };
    }
    for (final f in widget.fields.where((f) => f.required)) {
      if (_values[f.key] == null) {
        toast(context, '${f.label} is required.', error: true);
        return;
      }
    }
    Navigator.pop(context, _values);
  }

  Widget _field(FieldSpec f) {
    final label = '${f.label}${f.required ? ' *' : ''}';
    switch (f.kind) {
      case FieldKind.toggle:
        return SwitchListTile(
          contentPadding: EdgeInsets.zero,
          title: Text(f.label),
          subtitle: f.help == null ? null : Text(f.help!),
          value: _values[f.key] as bool? ?? false,
          onChanged: (v) => setState(() => _values[f.key] = v),
        );
      case FieldKind.choice:
        return DropdownButtonFormField<String>(
          initialValue: f.options.containsKey(_values[f.key]) ? _values[f.key] as String : null,
          decoration: InputDecoration(labelText: label, helperText: f.help),
          items: [for (final e in f.options.entries) DropdownMenuItem(value: e.key, child: Text(e.value))],
          onChanged: (v) => setState(() => _values[f.key] = v),
        );
      case FieldKind.source:
        return _SourceField(value: _values[f.key] as String?, onChanged: (v) => setState(() => _values[f.key] = v));
      default:
        final numeric = f.kind == FieldKind.integer || f.kind == FieldKind.decimal;
        return TextFormField(
          controller: _text[f.key],
          maxLines: f.kind == FieldKind.multiline ? 4 : 1,
          keyboardType: numeric ? const TextInputType.numberWithOptions(decimal: true) : null,
          inputFormatters: f.kind == FieldKind.integer
              ? [FilteringTextInputFormatter.digitsOnly]
              : f.kind == FieldKind.decimal
              ? [FilteringTextInputFormatter.allow(RegExp(r'[0-9.\-]'))]
              : null,
          decoration: InputDecoration(
            labelText: label,
            helperText: f.kind == FieldKind.list ? (f.help ?? 'Separate with commas') : f.help,
          ),
          validator: (v) {
            final t = (v ?? '').trim();
            if (f.required && t.isEmpty) return 'Required';
            if (t.isEmpty) return null;
            if (f.kind == FieldKind.integer && int.tryParse(t) == null) return 'Whole number';
            if (f.kind == FieldKind.decimal && double.tryParse(t) == null) return 'Number';
            return null;
          },
        );
    }
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: Text(widget.title),
    content: SizedBox(
      width: 520,
      child: Form(
        key: _form,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              for (final f in widget.fields) Padding(padding: const EdgeInsets.only(bottom: 14), child: _field(f)),
            ],
          ),
        ),
      ),
    ),
    actions: [
      TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
      FilledButton(onPressed: _save, child: const Text('Save')),
    ],
  );
}

class _SourceField extends ConsumerWidget {
  const _SourceField({required this.value, required this.onChanged});
  final String? value;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sources = ref.watch(sourcesProvider).value ?? const [];
    return Row(
      children: [
        Expanded(
          child: DropdownButtonFormField<String>(
            isExpanded: true,
            initialValue: sources.any((s) => s['id'] == value) ? value : null,
            decoration: const InputDecoration(
              labelText: 'Official source *',
              helperText: 'Required before submitting for review',
            ),
            items: [
              for (final s in sources)
                DropdownMenuItem(
                  value: s['id'] as String,
                  child: Text(
                    '${s['title']}${s['page_numbers'] != null ? ' (p. ${s['page_numbers']})' : ''}',
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
            ],
            onChanged: onChanged,
          ),
        ),
        const SizedBox(width: 8),
        IconButton.outlined(
          tooltip: 'Add a new source',
          icon: const Icon(Icons.add_link),
          onPressed: () async {
            final id = await addSource(context, ref);
            if (id != null) onChanged(id);
          },
        ),
      ],
    );
  }
}

const sourceFields = [
  FieldSpec(
    'kind',
    'Type',
    FieldKind.choice,
    required: true,
    options: {
      'pdf_prospectus': 'Official prospectus (PDF)',
      'web_page': 'Official web page',
      'official_notice': 'Official notice / advertisement',
      'email_from_university': 'Email from the university',
      'phone_call_note': 'Phone call with admissions office',
    },
  ),
  FieldSpec('title', 'Title', FieldKind.text, required: true, help: 'e.g. "UET Lahore Undergraduate Prospectus 2027"'),
  FieldSpec('url', 'Link', FieldKind.text, help: 'Must start with https://'),
  FieldSpec('page_numbers', 'Page numbers', FieldKind.text),
  FieldSpec('publisher', 'Published by', FieldKind.text),
];

Future<String?> addSource(BuildContext context, WidgetRef ref) async {
  final values = await showFormDialog(
    context,
    title: 'Add official source',
    fields: sourceFields,
    initial: {'kind': 'pdf_prospectus'},
  );
  if (values == null) return null;
  try {
    final r = await ref.read(apiProvider).post('/v1/admin/sources', {...values, 'is_official': true}) as Json;
    ref.invalidate(sourcesProvider);
    return r['id'] as String;
  } catch (e) {
    if (context.mounted) toast(context, e.toString(), error: true);
    return null;
  }
}

// ------------------------------------------------------------------ layout

class PageScaffold extends StatelessWidget {
  const PageScaffold({super.key, required this.title, required this.child, this.actions = const [], this.breadcrumb});
  final String title;
  final Widget child;
  final List<Widget> actions;
  final Widget? breadcrumb;

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(24, 20, 24, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ?breadcrumb,
                Row(
                  children: [
                    Expanded(child: Text(title, style: Theme.of(context).textTheme.headlineSmall)),
                    ...actions,
                  ],
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          Expanded(child: child),
        ],
      ),
    ),
  );
}

class AsyncBody<T> extends StatelessWidget {
  const AsyncBody(this.value, {super.key, required this.builder, this.onRetry});
  final AsyncValue<T> value;
  final Widget Function(T) builder;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) => value.when(
    data: builder,
    loading: () => const Center(child: CircularProgressIndicator()),
    error: (e, _) => Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(e.toString()),
          if (onRetry != null) TextButton(onPressed: onRetry, child: const Text('Try again')),
        ],
      ),
    ),
  );
}
