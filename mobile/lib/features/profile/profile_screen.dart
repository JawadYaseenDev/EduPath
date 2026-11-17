import 'dart:convert';

import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../core/format.dart';
import '../../data/models.dart';
import '../../state/providers.dart';
import '../../widgets/common.dart';
import 'forms.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(profileProvider);
    final reference = ref.watch(referenceProvider);
    final user = ref.watch(authProvider).user;
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: switch ((profile, reference)) {
        (AsyncData(value: final p), AsyncData(value: final r)) => ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(p.fullName ?? 'Student', style: Theme.of(context).textTheme.headlineSmall),
              Text(user?.email ?? ''),
              const SizedBox(height: 12),
              LinearProgressIndicator(value: p.completeness.percent / 100),
              const SizedBox(height: 4),
              Text('Profile ${p.completeness.percent}% complete',
                  style: Theme.of(context).textTheme.bodySmall),
              const SectionTitle('Your details'),
              _Tile(Icons.person_outline, 'About you',
                  [p.fullName, r.city(p.currentCityId)?.name, p.gender == null ? null : titleCase(p.gender!)]
                      .whereType<String>()
                      .join(' · '),
                  '/edit/personal'),
              _Tile(Icons.menu_book_outlined, 'Matric / O-Levels', _qual(p.qualification('SSC'), r),
                  '/edit/qualification/SSC'),
              _Tile(Icons.school_outlined, 'Intermediate / A-Levels / DAE', _qual(p.higherSecondary, r),
                  '/edit/qualification/HSSC'),
              _Tile(Icons.assignment_outlined, 'Entry tests',
                  p.testScores.isEmpty ? 'None added' : p.testScores.map((s) => s.testCode).join(', '),
                  '/edit/tests'),
              _Tile(Icons.interests_outlined, 'Interests',
                  p.preferences.fields.map(r.fieldName).join(', '), '/edit/interests'),
              _Tile(Icons.tune, 'Preferences',
                  p.preferences.maxFeePerSemester == null
                      ? 'No budget limit'
                      : 'Up to ${pkr(p.preferences.maxFeePerSemester)} per semester',
                  '/edit/preferences'),
              const SectionTitle('Account and privacy'),
              ListTile(
                leading: const Icon(Icons.download_outlined),
                title: const Text('Download my data'),
                onTap: () => _export(context, ref),
              ),
              ListTile(
                leading: const Icon(Icons.logout),
                title: const Text('Log out'),
                onTap: () => _logout(context, ref),
              ),
              ListTile(
                leading: const Icon(Icons.devices),
                title: const Text('Log out on all devices'),
                onTap: () async {
                  try {
                    await ref.read(apiProvider).logoutEverywhere();
                  } finally {
                    await ref.read(authProvider.notifier).logout();
                    if (context.mounted) context.go('/welcome');
                  }
                },
              ),
              ListTile(
                leading: Icon(Icons.delete_forever, color: Theme.of(context).colorScheme.error),
                title: Text('Delete my account',
                    style: TextStyle(color: Theme.of(context).colorScheme.error)),
                onTap: () => _delete(context, ref),
              ),
              const SizedBox(height: 16),
              const InfoBanner(
                  'Where our information comes from: university data is entered by our team from '
                  'official prospectuses and websites, and shows when it was last checked. '
                  'Records marked SAMPLE DATA are for testing only.'),
            ],
          ),
        (AsyncError(:final error), _) || (_, AsyncError(:final error)) => ErrorView(error,
            onRetry: () => ref.invalidate(profileProvider)),
        _ => const Loading(),
      },
    );
  }

  static String _qual(Qualification? q, Reference r) {
    if (q == null) return 'Not added';
    final pct = q.ibccPercentage != null
        ? 'IBCC ${percent(q.ibccPercentage)}'
        : q.resultStatus == 'part1_only'
            ? 'Part-I ${percent(q.part1Percentage)}'
            : q.resultStatus == 'awaited'
                ? 'Result awaited'
                : percent(q.percentage);
    return '${r.groupName(q.groupCode)} · $pct';
  }

  Future<void> _logout(BuildContext context, WidgetRef ref) async {
    await ref.read(authProvider.notifier).logout();
    if (context.mounted) context.go('/welcome');
  }

  Future<void> _export(BuildContext context, WidgetRef ref) async {
    try {
      final data = await ref.read(apiProvider).exportData();
      final text = const JsonEncoder.withIndent('  ').convert(data);
      if (!context.mounted) return;
      await showDialog<void>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Your data'),
          content: SizedBox(
              width: 500,
              child: SingleChildScrollView(child: SelectableText(text, style: const TextStyle(fontSize: 12)))),
          actions: [
            TextButton(
              onPressed: () {
                Clipboard.setData(ClipboardData(text: text));
                Navigator.pop(ctx);
                showMessage(context, 'Copied to clipboard');
              },
              child: const Text('Copy'),
            ),
            FilledButton(onPressed: () => Navigator.pop(ctx), child: const Text('Close')),
          ],
        ),
      );
    } catch (e) {
      if (context.mounted) showMessage(context, e.toString());
    }
  }

  Future<void> _delete(BuildContext context, WidgetRef ref) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete your account?'),
        content: const Text('This permanently deletes your account, profile, marks, shortlist and '
            'results. This cannot be undone.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Theme.of(ctx).colorScheme.error),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Delete permanently'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(apiProvider).deleteAccount();
      await ref.read(authProvider.notifier).logout();
      if (context.mounted) {
        context.go('/welcome');
        showMessage(context, 'Your account has been deleted.');
      }
    } catch (e) {
      if (context.mounted) showMessage(context, e.toString());
    }
  }
}

class _Tile extends StatelessWidget {
  const _Tile(this.icon, this.title, this.subtitle, this.route);
  final IconData icon;
  final String title;
  final String subtitle;
  final String route;

  @override
  Widget build(BuildContext context) => Card(
        margin: const EdgeInsets.only(bottom: 8),
        child: ListTile(
          leading: Icon(icon),
          title: Text(title),
          subtitle: Text(subtitle.isEmpty ? '-' : subtitle),
          trailing: const Icon(Icons.edit_outlined),
          onTap: () => context.push(route),
        ),
      );
}

/// Single-section edit screen that reuses the wizard forms.
class EditSectionScreen extends ConsumerWidget {
  const EditSectionScreen({super.key, required this.section, this.level});
  final String section; // personal | qualification | interests | preferences | tests
  final String? level;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(profileProvider);
    final reference = ref.watch(referenceProvider);
    final title = switch (section) {
      'personal' => 'About you',
      'qualification' => level == 'SSC' ? 'Matric / O-Levels' : 'Intermediate / A-Levels / DAE',
      'interests' => 'Interests',
      'preferences' => 'Preferences',
      _ => 'Entry tests',
    };
    void done() {
      showMessage(context, 'Saved');
      if (context.canPop()) context.pop();
    }

    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: switch ((profile, reference)) {
        (AsyncData(value: final p), AsyncData(value: final r)) => Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 640),
              child: ListView(padding: const EdgeInsets.all(20), children: [
                switch (section) {
                  'personal' => PersonalForm(profile: p, reference: r, onDone: done),
                  'qualification' =>
                    QualificationForm(slot: level ?? 'HSSC', profile: p, reference: r, onDone: done),
                  'interests' => InterestsForm(profile: p, reference: r, onDone: done),
                  'preferences' => PreferencesForm(profile: p, reference: r, onDone: done),
                  _ => TestScoresForm(profile: p, reference: r),
                },
              ]),
            ),
          ),
        (AsyncError(:final error), _) || (_, AsyncError(:final error)) => ErrorView(error),
        _ => const Loading(),
      },
    );
  }
}
