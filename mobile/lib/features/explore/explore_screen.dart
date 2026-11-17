import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../../core/format.dart';
import '../../data/models.dart';
import '../../state/providers.dart';
import '../../widgets/common.dart';

/// Search and filter all programmes (FR-05). Works without an account.
class ExploreScreen extends ConsumerStatefulWidget {
  const ExploreScreen({super.key});

  @override
  ConsumerState<ExploreScreen> createState() => _ExploreScreenState();
}

class _ExploreScreenState extends ConsumerState<ExploreScreen> {
  final _search = TextEditingController();
  Timer? _debounce;
  String? _field;
  String? _region;
  String? _sector;
  int? _maxFee;
  String? _hostelFor;
  String _sort = 'name';
  Future<List<OfferingCard>>? _results;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _search.dispose();
    super.dispose();
  }

  void _load() {
    setState(() {
      _results = ref.read(apiProvider).searchProgrammes({
        if (_search.text.trim().isNotEmpty) 'q': _search.text.trim(),
        'field': ?_field,
        'region': ?_region,
        'sector': ?_sector,
        'max_fee': ?_maxFee,
        'hostel_for': ?_hostelFor,
        'sort': _sort,
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final reference = ref.watch(referenceProvider).value;
    final signedIn = ref.watch(authProvider).status == AuthStatus.signedIn;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Explore'),
        actions: [
          if (!signedIn)
            TextButton(onPressed: () => context.go('/welcome'), child: const Text('Sign in')),
        ],
      ),
      body: Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          child: SearchBar(
            controller: _search,
            hintText: 'Search programme, university or city',
            leading: const Icon(Icons.search),
            trailing: [
              if (_search.text.isNotEmpty)
                IconButton(
                  tooltip: 'Clear',
                  icon: const Icon(Icons.clear),
                  onPressed: () {
                    _search.clear();
                    _load();
                  },
                ),
            ],
            onChanged: (_) {
              _debounce?.cancel();
              _debounce = Timer(const Duration(milliseconds: 350), _load);
            },
          ),
        ),
        SizedBox(
          height: 56,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            children: [
              _menuChip<String>(
                label: _field == null ? 'Field' : reference?.fieldName(_field!) ?? _field!,
                selected: _field != null,
                options: {for (final f in reference?.fields ?? <Named>[]) f.code: f.name},
                onSelected: (v) => _field = v,
              ),
              _menuChip<String>(
                label: _region == null ? 'Province' : reference?.regionName(_region!) ?? _region!,
                selected: _region != null,
                options: {for (final r in reference?.regions ?? <Named>[]) r.code: r.name},
                onSelected: (v) => _region = v,
              ),
              _menuChip<String>(
                label: _sector == null ? 'Type' : sectorLabel(_sector),
                selected: _sector != null,
                options: {for (final s in const ['public', 'private', 'semi_government']) s: sectorLabel(s)},
                onSelected: (v) => _sector = v,
              ),
              _menuChip<int>(
                label: _maxFee == null ? 'Fee' : 'Up to ${pkr(_maxFee)}',
                selected: _maxFee != null,
                options: {for (final f in const [25000, 50000, 75000, 100000, 150000]) f: 'Up to ${pkr(f)}/sem'},
                onSelected: (v) => _maxFee = v,
              ),
              _menuChip<String>(
                label: _hostelFor == null ? 'Hostel' : (_hostelFor == 'female' ? 'Girls hostel' : 'Boys hostel'),
                selected: _hostelFor != null,
                options: const {'female': 'Girls hostel', 'male': 'Boys hostel'},
                onSelected: (v) => _hostelFor = v,
              ),
              _menuChip<String>(
                label: _sort == 'fee' ? 'Sort: fee' : 'Sort: name',
                selected: false,
                options: const {'name': 'Sort by name', 'fee': 'Sort by fee (low to high)'},
                onSelected: (v) => _sort = v ?? 'name',
                allowClear: false,
              ),
            ],
          ),
        ),
        Expanded(
          child: FutureBuilder<List<OfferingCard>>(
            future: _results,
            builder: (context, snap) {
              if (snap.hasError) return ErrorView(snap.error!, onRetry: _load);
              if (!snap.hasData) return const Loading();
              final items = snap.data!;
              if (items.isEmpty) {
                return const Center(
                  child: Padding(
                    padding: EdgeInsets.all(24),
                    child: Text('No programmes match your search. Try removing a filter.',
                        textAlign: TextAlign.center),
                  ),
                );
              }
              return ListView.separated(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                itemCount: items.length + 1,
                separatorBuilder: (_, _) => const SizedBox(height: 10),
                itemBuilder: (context, i) {
                  if (i == 0) {
                    return Text('${items.length} programme${items.length == 1 ? '' : 's'}',
                        style: Theme.of(context).textTheme.labelLarge);
                  }
                  final c = items[i - 1];
                  return OfferingTile(c, onTap: () => context.push('/programme/${c.offeringId}'));
                },
              );
            },
          ),
        ),
      ]),
    );
  }

  Widget _menuChip<T>({
    required String label,
    required bool selected,
    required Map<T, String> options,
    required void Function(T?) onSelected,
    bool allowClear = true,
  }) =>
      Padding(
        padding: const EdgeInsets.only(right: 8),
        child: MenuAnchor(
          menuChildren: [
            if (allowClear && selected)
              MenuItemButton(
                leadingIcon: const Icon(Icons.clear),
                onPressed: () {
                  onSelected(null);
                  _load();
                },
                child: const Text('Any'),
              ),
            for (final e in options.entries)
              MenuItemButton(
                onPressed: () {
                  onSelected(e.key);
                  _load();
                },
                child: Text(e.value),
              ),
          ],
          builder: (context, controller, _) => FilterChip(
            label: Text(label),
            selected: selected,
            onSelected: (_) => controller.isOpen ? controller.close() : controller.open(),
            avatar: selected ? null : const Icon(Icons.arrow_drop_down, size: 18),
          ),
        ),
      );
}

class UniversityScreen extends ConsumerWidget {
  const UniversityScreen({super.key, required this.universityId});
  final String universityId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detail = ref.watch(universityProvider(universityId));
    return Scaffold(
      appBar: AppBar(title: const Text('University')),
      body: detail.when(
        loading: () => const Loading(),
        error: (e, _) => ErrorView(e, onRetry: () => ref.invalidate(universityProvider(universityId))),
        data: (u) {
          final t = Theme.of(context).textTheme;
          return ListView(padding: const EdgeInsets.all(16), children: [
            if (u.isDemo) ...[
              const InfoBanner('Sample data for testing. This is not a real university.',
                  icon: Icons.science_outlined),
              const SizedBox(height: 12),
            ],
            Text(u.name, style: t.headlineSmall),
            const SizedBox(height: 4),
            Text('${sectorLabel(u.sector)} · ${genderPolicyLabel(u.genderPolicy)}'),
            if (u.description != null) ...[const SizedBox(height: 8), Text(u.description!)],
            const SizedBox(height: 12),
            Wrap(spacing: 8, children: [
              OutlinedButton.icon(
                onPressed: () => openLink(context, u.websiteUrl),
                icon: const Icon(Icons.language),
                label: const Text('Website'),
              ),
              FilledButton.icon(
                onPressed: () => openLink(context, u.admissionsUrl ?? u.websiteUrl),
                icon: const Icon(Icons.open_in_new),
                label: const Text('Admissions'),
              ),
            ]),
            const SectionTitle('Campuses'),
            for (final c in u.campuses)
              Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  leading: const Icon(Icons.location_city),
                  title: Text('${c['name']} · ${c['city']}'),
                  subtitle: Text([
                    genderPolicyLabel(c['gender_policy'] as String?),
                    for (final h in (c['hostels'] as List).cast<Json>())
                      '${h['for_gender'] == 'female' ? 'Girls' : 'Boys'} hostel: ${titleCase(h['availability'] as String)}',
                  ].join(' · ')),
                ),
              ),
            SectionTitle('Programmes (${u.programmes.length})'),
            for (final p in u.programmes)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: OfferingTile(p, onTap: () => context.push('/programme/${p.offeringId}')),
              ),
            if (u.verifiedAt != null)
              Text('Last verified ${niceDate(u.verifiedAt)}', style: t.bodySmall),
          ]);
        },
      ),
    );
  }
}
