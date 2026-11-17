// Profile forms used by both the setup wizard and the profile edit screens (FR-02).
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../../core/format.dart';
import '../../data/models.dart';
import '../../state/providers.dart';
import '../../widgets/common.dart';

/// Shared Save/Next button with busy state and error display.
mixin _Submitting<T extends ConsumerStatefulWidget> on ConsumerState<T> {
  bool busy = false;
  String? error;

  Future<void> submit(Future<void> Function() action, VoidCallback onDone) async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await action();
      if (mounted) onDone();
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Widget submitArea(String label, VoidCallback? onPressed) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (error != null) ...[
            InfoBanner(error!, icon: Icons.error_outline, warning: true),
            const SizedBox(height: 12),
          ],
          FilledButton(
            onPressed: busy ? null : onPressed,
            child: busy
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : Text(label),
          ),
        ],
      );
}

Widget _label(BuildContext context, String text, {String? help}) => Padding(
      padding: const EdgeInsets.only(top: 16, bottom: 8),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(text, style: Theme.of(context).textTheme.titleSmall),
        if (help != null)
          Text(help,
              style: Theme.of(context)
                  .textTheme
                  .bodySmall
                  ?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant)),
      ]),
    );

// ===================================================================== personal

class PersonalForm extends ConsumerStatefulWidget {
  const PersonalForm({super.key, required this.profile, required this.reference,
      required this.onDone, this.submitLabel = 'Save'});
  final Profile profile;
  final Reference reference;
  final VoidCallback onDone;
  final String submitLabel;

  @override
  ConsumerState<PersonalForm> createState() => _PersonalFormState();
}

class _PersonalFormState extends ConsumerState<PersonalForm> with _Submitting {
  final _form = GlobalKey<FormState>();
  late final _name = TextEditingController(text: widget.profile.fullName);
  late final _phone = TextEditingController(text: widget.profile.phone);
  late String? _gender = widget.profile.gender;
  late String? _cityId = widget.profile.currentCityId;
  late String? _domicile = widget.profile.domicileRegionCode;
  late DateTime? _dob = DateTime.tryParse(widget.profile.dateOfBirth ?? '');

  @override
  void dispose() {
    _name.dispose();
    _phone.dispose();
    super.dispose();
  }

  void _save() {
    if (!_form.currentState!.validate()) return;
    if (_gender == null || _cityId == null) {
      setState(() => error = 'Please choose your gender and current city.');
      return;
    }
    submit(
      () => ref.read(profileProvider.notifier).updatePersonal({
        'full_name': _name.text.trim(),
        'phone': _phone.text.trim().isEmpty ? null : _phone.text.trim(),
        'gender': _gender,
        'date_of_birth': _dob?.toIso8601String().substring(0, 10),
        'current_city_id': _cityId,
        'domicile_region_code': _domicile,
      }),
      widget.onDone,
    );
  }

  @override
  Widget build(BuildContext context) {
    final ref_ = widget.reference;
    return Form(
      key: _form,
      autovalidateMode: AutovalidateMode.onUserInteraction,
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        TextFormField(
          controller: _name,
          decoration: const InputDecoration(labelText: 'Full name'),
          textCapitalization: TextCapitalization.words,
          validator: (v) => (v ?? '').trim().length < 2 ? 'Please enter your full name.' : null,
        ),
        _label(context, 'Gender',
            help: 'Some campuses and hostels are for women or men only.'),
        SegmentedButton<String>(
          emptySelectionAllowed: true,
          segments: const [
            ButtonSegment(value: 'female', label: Text('Female')),
            ButtonSegment(value: 'male', label: Text('Male')),
            ButtonSegment(value: 'other', label: Text('Other')),
          ],
          selected: {?_gender},
          onSelectionChanged: (s) => setState(() => _gender = s.firstOrNull),
        ),
        _label(context, 'Date of birth (optional)', help: 'Some programmes have an age limit.'),
        OutlinedButton.icon(
          icon: const Icon(Icons.cake_outlined),
          label: Text(_dob == null ? 'Choose date' : niceDate(_dob!.toIso8601String())),
          onPressed: () async {
            final picked = await showDatePicker(
              context: context,
              initialDate: _dob ?? DateTime(DateTime.now().year - 18),
              firstDate: DateTime(1970),
              lastDate: DateTime.now(),
            );
            if (picked != null) setState(() => _dob = picked);
          },
        ),
        _label(context, 'Current city'),
        DropdownMenu<String>(
          initialSelection: _cityId,
          expandedInsets: EdgeInsets.zero,
          enableFilter: true,
          requestFocusOnTap: true,
          hintText: 'Search your city',
          dropdownMenuEntries: [
            for (final c in ref_.cities)
              DropdownMenuEntry(value: c.id, label: '${c.name} (${ref_.regionName(c.regionCode)})'),
          ],
          onSelected: (v) => setState(() => _cityId = v),
        ),
        _label(context, 'Domicile (province / region)',
            help: 'Some public universities reserve seats by domicile.'),
        DropdownMenu<String>(
          initialSelection: _domicile,
          expandedInsets: EdgeInsets.zero,
          hintText: 'Choose your domicile',
          dropdownMenuEntries: [
            for (final r in ref_.regions) DropdownMenuEntry(value: r.code, label: r.name),
          ],
          onSelected: (v) => setState(() => _domicile = v),
        ),
        const SizedBox(height: 16),
        TextFormField(
          controller: _phone,
          keyboardType: TextInputType.phone,
          decoration: const InputDecoration(labelText: 'Phone number (optional)'),
        ),
        const SizedBox(height: 24),
        submitArea(widget.submitLabel, _save),
      ]),
    );
  }
}

// ===================================================================== qualification

/// [slot] is "SSC" (Matric / O-Level) or "HSSC" (Intermediate / A-Level / DAE).
class QualificationForm extends ConsumerStatefulWidget {
  const QualificationForm({super.key, required this.slot, required this.profile,
      required this.reference, required this.onDone, this.submitLabel = 'Save'});
  final String slot;
  final Profile profile;
  final Reference reference;
  final VoidCallback onDone;
  final String submitLabel;

  @override
  ConsumerState<QualificationForm> createState() => _QualificationFormState();
}

class _QualificationFormState extends ConsumerState<QualificationForm> with _Submitting {
  final _form = GlobalKey<FormState>();
  late final Qualification? _existing = widget.slot == 'SSC'
      ? widget.profile.qualification('SSC')
      : widget.profile.higherSecondary;
  late String? _type = _existing?.typeCode;
  late String? _group = _existing?.groupCode;
  late String? _board = _existing?.boardId;
  late String _status = _existing?.resultStatus ?? 'final';
  late bool _ibccOfficial = _existing?.ibccIsOfficial ?? false;
  late Set<String> _subjects = {...?_existing?.subjects.map((s) => s.code)};
  late final _year = TextEditingController(text: _existing?.passingYear?.toString());
  late final _obtained = TextEditingController(text: _num(_existing?.obtained));
  late final _total = TextEditingController(text: _num(_existing?.total));
  late final _p1Obtained = TextEditingController(text: _num(_existing?.part1Obtained));
  late final _p1Total = TextEditingController(text: _num(_existing?.part1Total));
  late final _ibcc = TextEditingController(text: _num(_existing?.ibccPercentage));

  static String? _num(double? v) =>
      v == null ? null : (v == v.roundToDouble() ? v.toInt().toString() : v.toString());

  @override
  void dispose() {
    for (final c in [_year, _obtained, _total, _p1Obtained, _p1Total, _ibcc]) {
      c.dispose();
    }
    super.dispose();
  }

  Reference get _ref => widget.reference;
  bool get _higher => widget.slot == 'HSSC';
  QualTypeRef? get _typeRef => _ref.types.where((t) => t.code == _type).firstOrNull;
  GroupRef? get _groupRef => _ref.groups.where((g) => g.code == _group).firstOrNull;
  bool get _usesIbcc => _typeRef?.usesIbcc ?? false;

  List<QualTypeRef> get _types => _higher
      ? _ref.types.where((t) => t.level == 'HSSC' || t.level == 'DIPLOMA').toList()
      : _ref.typesFor('SSC');

  List<BoardRef> get _boards {
    final kinds = _usesIbcc
        ? {'foreign'}
        : _typeRef?.level == 'DIPLOMA'
            ? {'technical'}
            : {'bise', 'federal', 'private'};
    return _ref.boards.where((b) => kinds.contains(b.kind)).toList();
  }

  void _pickGroup(String? code) {
    setState(() {
      _group = code;
      final g = _groupRef;
      if (g == null) return;
      // Pre-select the usual subjects: all compulsory + the first of each "pick one" set.
      final seen = <String>{};
      _subjects = {
        for (final s in g.subjects)
          if (s.isCompulsory || (s.choiceSet != null && seen.add(s.choiceSet!))) s.code,
      };
    });
  }

  double? _parse(TextEditingController c) => double.tryParse(c.text.trim());

  String? _livePercent() {
    final o = _parse(_status == 'part1_only' ? _p1Obtained : _obtained);
    final t = _parse(_status == 'part1_only' ? _p1Total : _total);
    if (o == null || t == null || t <= 0 || o > t) return null;
    return percent(o / t * 100);
  }

  void _save() {
    if (_type == null || _group == null) {
      setState(() => error = 'Please choose your qualification and group.');
      return;
    }
    if (!_form.currentState!.validate()) return;
    final level = _typeRef!.level;
    final body = {
      'type_code': _type,
      'group_code': _group,
      'board_id': _board,
      'passing_year': int.tryParse(_year.text.trim()),
      'result_status': _higher && !_usesIbcc ? _status : 'final',
      'obtained_marks': _status == 'final' || !_higher ? _parse(_obtained) : null,
      'total_marks': _status == 'final' || !_higher ? _parse(_total) : null,
      'part1_obtained': _status == 'part1_only' ? _parse(_p1Obtained) : null,
      'part1_total': _status == 'part1_only' ? _parse(_p1Total) : null,
      'ibcc_percentage': _usesIbcc ? _parse(_ibcc) : null,
      'ibcc_is_official': _usesIbcc && _ibccOfficial,
      'subjects': [for (final s in _subjects) {'code': s}],
    };
    if (_usesIbcc) {
      body['obtained_marks'] = null;
      body['total_marks'] = null;
    }
    submit(() async {
      final notifier = ref.read(profileProvider.notifier);
      await notifier.saveQualification(body);
      // A student has either Intermediate/A-Level (HSSC) or DAE (DIPLOMA), not both.
      if (_higher) {
        final other = level == 'HSSC' ? 'DIPLOMA' : 'HSSC';
        if (widget.profile.qualification(other) != null) {
          await notifier.deleteQualification(other);
        }
      }
    }, widget.onDone);
  }

  String? _marksValidator(String? v, {bool required = true}) {
    final value = double.tryParse((v ?? '').trim());
    if (value == null) return required ? 'Required' : null;
    if (value < 0) return 'Cannot be negative';
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final groups = _type == null ? <GroupRef>[] : _ref.groupsFor(_type!);
    final subjectChoices = _groupRef == null
        ? <String>[]
        : (_groupRef!.allowsCustomSubjects
            ? _ref.subjects.map((s) => s.code).toList()
            : _groupRef!.subjects.map((s) => s.code).toList());
    final live = _livePercent();
    final numberInput = [FilteringTextInputFormatter.allow(RegExp(r'[0-9.]'))];

    return Form(
      key: _form,
      autovalidateMode: AutovalidateMode.onUserInteraction,
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        _label(context, 'Qualification'),
        DropdownMenu<String>(
          key: ValueKey('type-${widget.slot}'),
          initialSelection: _type,
          expandedInsets: EdgeInsets.zero,
          hintText: _higher ? 'Intermediate, A-Levels or DAE' : 'Matric or O-Levels',
          dropdownMenuEntries: [for (final t in _types) DropdownMenuEntry(value: t.code, label: t.name)],
          onSelected: (v) => setState(() {
            _type = v;
            _group = null;
            _board = null;
            _subjects = {};
            final only = v == null ? const <GroupRef>[] : _ref.groupsFor(v);
            if (only.length == 1) _pickGroup(only.first.code);
          }),
        ),
        if (groups.length > 1) ...[
          _label(context, 'Group / stream'),
          DropdownMenu<String>(
            key: ValueKey('group-$_type'),
            initialSelection: _group,
            expandedInsets: EdgeInsets.zero,
            hintText: 'Choose your group',
            dropdownMenuEntries: [for (final g in groups) DropdownMenuEntry(value: g.code, label: g.name)],
            onSelected: _pickGroup,
          ),
        ],
        if (_type != null) ...[
          _label(context, 'Board or examining body'),
          DropdownMenu<String>(
            key: ValueKey('board-$_type'),
            initialSelection: _board,
            expandedInsets: EdgeInsets.zero,
            enableFilter: true,
            requestFocusOnTap: true,
            hintText: 'Search your board',
            dropdownMenuEntries: [
              for (final b in _boards) DropdownMenuEntry(value: b.id, label: b.shortName),
            ],
            onSelected: (v) => setState(() => _board = v),
          ),
        ],
        if (_groupRef != null) ...[
          _label(context, 'Subjects you studied',
              help: 'We selected the usual subjects for your group. Change them if yours were different.'),
          Wrap(spacing: 8, runSpacing: 8, children: [
            for (final code in subjectChoices)
              FilterChip(
                label: Text(_ref.subjectName(code)),
                selected: _subjects.contains(code),
                onSelected: (on) => setState(() => on ? _subjects.add(code) : _subjects.remove(code)),
              ),
          ]),
        ],
        if (_type != null && _higher && !_usesIbcc) ...[
          _label(context, 'Result status',
              help: 'Many students apply before their final result. Choose "Part-I only" to use your Part-I marks.'),
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'final', label: Text('Final result')),
              ButtonSegment(value: 'part1_only', label: Text('Part-I only')),
              ButtonSegment(value: 'awaited', label: Text('Not yet')),
            ],
            selected: {_status},
            onSelectionChanged: (s) => setState(() => _status = s.first),
          ),
        ],
        if (_type != null && _usesIbcc) ...[
          _label(context, 'IBCC equivalence percentage',
              help: 'A-Level and O-Level grades are converted to a percentage by IBCC.'),
          TextFormField(
            controller: _ibcc,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            inputFormatters: numberInput,
            decoration: const InputDecoration(labelText: 'Equivalence %', suffixText: '%'),
            validator: (v) {
              final value = double.tryParse((v ?? '').trim());
              if (value == null) return null;
              return value > 100 ? 'Cannot be more than 100' : null;
            },
          ),
          CheckboxListTile(
            value: _ibccOfficial,
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            onChanged: (v) => setState(() => _ibccOfficial = v ?? false),
            title: const Text('I have the official IBCC equivalence certificate'),
            subtitle: const Text('If not, results that depend on it will show as "potentially eligible".'),
          ),
        ],
        if (_type != null && !_usesIbcc && (_status == 'final' || !_higher)) ...[
          _label(context, 'Marks'),
          Row(children: [
            Expanded(
              child: TextFormField(
                controller: _obtained,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                inputFormatters: numberInput,
                decoration: const InputDecoration(labelText: 'Obtained marks'),
                validator: (v) {
                  final base = _marksValidator(v);
                  if (base != null) return base;
                  final t = _parse(_total);
                  if (t != null && double.parse(v!.trim()) > t) {
                    return 'Cannot be more than total';
                  }
                  return null;
                },
                onChanged: (_) => setState(() {}),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: TextFormField(
                controller: _total,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                inputFormatters: numberInput,
                decoration: const InputDecoration(labelText: 'Total marks'),
                validator: _marksValidator,
                onChanged: (_) => setState(() {}),
              ),
            ),
          ]),
        ],
        if (_type != null && _status == 'part1_only' && _higher && !_usesIbcc) ...[
          _label(context, 'Part-I marks'),
          Row(children: [
            Expanded(
              child: TextFormField(
                controller: _p1Obtained,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                inputFormatters: numberInput,
                decoration: const InputDecoration(labelText: 'Part-I obtained'),
                validator: _marksValidator,
                onChanged: (_) => setState(() {}),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: TextFormField(
                controller: _p1Total,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                inputFormatters: numberInput,
                decoration: const InputDecoration(labelText: 'Part-I total'),
                validator: _marksValidator,
                onChanged: (_) => setState(() {}),
              ),
            ),
          ]),
        ],
        if (live != null)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text('Your percentage: $live',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    color: Theme.of(context).colorScheme.primary)),
          ),
        if (_type != null) ...[
          const SizedBox(height: 16),
          TextFormField(
            controller: _year,
            keyboardType: TextInputType.number,
            inputFormatters: [FilteringTextInputFormatter.digitsOnly],
            decoration: InputDecoration(
                labelText: _status == 'final' || !_higher ? 'Passing year' : 'Expected passing year'),
            validator: (v) {
              final y = int.tryParse((v ?? '').trim());
              if (y == null) return null;
              return (y < 1980 || y > DateTime.now().year + 2) ? 'Please enter a valid year' : null;
            },
          ),
        ],
        const SizedBox(height: 24),
        submitArea(widget.submitLabel, _save),
      ]),
    );
  }
}

// ===================================================================== interests

class InterestsForm extends ConsumerStatefulWidget {
  const InterestsForm({super.key, required this.profile, required this.reference,
      required this.onDone, this.submitLabel = 'Save'});
  final Profile profile;
  final Reference reference;
  final VoidCallback onDone;
  final String submitLabel;

  @override
  ConsumerState<InterestsForm> createState() => _InterestsFormState();
}

class _InterestsFormState extends ConsumerState<InterestsForm> with _Submitting {
  late final Set<String> _fields = {...widget.profile.preferences.fields};
  late final Set<String> _disciplines = {...widget.profile.preferences.disciplines};

  void _save() {
    if (_fields.isEmpty && _disciplines.isEmpty) {
      setState(() => error = 'Please choose at least one field you are interested in.');
      return;
    }
    // Keep only disciplines inside chosen fields.
    final keep = widget.reference.disciplines
        .where((d) => _disciplines.contains(d.code) && _fields.contains(d.fieldCode))
        .map((d) => d.code)
        .toList();
    final prefs = widget.profile.preferences.copyWith(fields: _fields.toList(), disciplines: keep);
    submit(() => ref.read(profileProvider.notifier).savePreferences(prefs), widget.onDone);
  }

  @override
  Widget build(BuildContext context) {
    final r = widget.reference;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      _label(context, 'Which fields interest you?', help: 'Choose one or more.'),
      Wrap(spacing: 8, runSpacing: 8, children: [
        for (final f in r.fields)
          FilterChip(
            label: Text(f.name),
            selected: _fields.contains(f.code),
            onSelected: (on) => setState(() => on ? _fields.add(f.code) : _fields.remove(f.code)),
          ),
      ]),
      for (final f in r.fields.where((f) => _fields.contains(f.code))) ...[
        _label(context, 'Programmes in ${f.name} (optional)',
            help: 'Leave empty to see all programmes in this field.'),
        Wrap(spacing: 8, runSpacing: 8, children: [
          for (final d in r.disciplines.where((d) => d.fieldCode == f.code))
            FilterChip(
              label: Text(d.name),
              selected: _disciplines.contains(d.code),
              onSelected: (on) =>
                  setState(() => on ? _disciplines.add(d.code) : _disciplines.remove(d.code)),
            ),
        ]),
      ],
      const SizedBox(height: 24),
      submitArea(widget.submitLabel, _save),
    ]);
  }
}

// ===================================================================== preferences

class PreferencesForm extends ConsumerStatefulWidget {
  const PreferencesForm({super.key, required this.profile, required this.reference,
      required this.onDone, this.submitLabel = 'Save'});
  final Profile profile;
  final Reference reference;
  final VoidCallback onDone;
  final String submitLabel;

  @override
  ConsumerState<PreferencesForm> createState() => _PreferencesFormState();
}

class _PreferencesFormState extends ConsumerState<PreferencesForm> with _Submitting {
  late Preferences _p = widget.profile.preferences;
  static const _quickBudgets = [25000, 50000, 75000, 100000, 150000];

  List<String> _toggle(List<String> list, String value, bool on) =>
      on ? [...list, value] : list.where((v) => v != value).toList();

  @override
  Widget build(BuildContext context) {
    final r = widget.reference;
    final fee = _p.maxFeePerSemester;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      _label(context, 'Preferred provinces / regions', help: 'Leave empty for all of Pakistan.'),
      Wrap(spacing: 8, runSpacing: 8, children: [
        for (final reg in r.regions)
          FilterChip(
            label: Text(reg.name),
            selected: _p.regions.contains(reg.code),
            onSelected: (on) => setState(() => _p = _p.copyWith(regions: _toggle(_p.regions, reg.code, on))),
          ),
      ]),
      _label(context, 'Budget per semester',
          help: fee == null ? 'No limit' : 'Up to ${pkr(fee)} per semester'),
      SwitchListTile(
        contentPadding: EdgeInsets.zero,
        title: const Text('Set a budget limit'),
        value: fee != null,
        onChanged: (on) => setState(() => _p = _p.copyWith(maxFeePerSemester: () => on ? 75000 : null)),
      ),
      if (fee != null) ...[
        Slider(
          value: fee.clamp(10000, 400000).toDouble(),
          min: 10000,
          max: 400000,
          divisions: 78,
          label: pkr(fee),
          onChanged: (v) => setState(() => _p = _p.copyWith(maxFeePerSemester: () => v.round())),
        ),
        Wrap(spacing: 8, children: [
          for (final b in _quickBudgets)
            ChoiceChip(
              label: Text('${b ~/ 1000}k'),
              selected: fee == b,
              onSelected: (_) => setState(() => _p = _p.copyWith(maxFeePerSemester: () => b)),
            ),
        ]),
        _label(context, 'My budget includes'),
        SegmentedButton<String>(
          segments: const [
            ButtonSegment(value: 'tuition_only', label: Text('Tuition only')),
            ButtonSegment(value: 'university_charges', label: Text('All charges')),
            ButtonSegment(value: 'with_hostel', label: Text('+ Hostel')),
          ],
          selected: {_p.budgetIncludes},
          onSelectionChanged: (s) => setState(() => _p = _p.copyWith(budgetIncludes: s.first)),
        ),
      ],
      _label(context, 'University type', help: 'Leave empty for all types.'),
      Wrap(spacing: 8, children: [
        for (final s in const ['public', 'private', 'semi_government'])
          FilterChip(
            label: Text(sectorLabel(s)),
            selected: _p.sectors.contains(s),
            onSelected: (on) => setState(() => _p = _p.copyWith(sectors: _toggle(_p.sectors, s, on))),
          ),
      ]),
      _label(context, 'Hostel'),
      SegmentedButton<String>(
        segments: const [
          ButtonSegment(value: 'none', label: Text('Not needed')),
          ButtonSegment(value: 'needed', label: Text('Needed')),
          ButtonSegment(value: 'on_campus_only', label: Text('On campus')),
        ],
        selected: {_p.hostelNeed},
        onSelectionChanged: (s) => setState(() => _p = _p.copyWith(hostelNeed: s.first)),
      ),
      _label(context, 'Campus type'),
      SegmentedButton<String>(
        segments: const [
          ButtonSegment(value: 'any', label: Text('Any')),
          ButtonSegment(value: 'coeducation', label: Text('Co-education')),
          ButtonSegment(value: 'single_gender', label: Text('Single gender')),
        ],
        selected: {_p.genderCampusPref},
        onSelectionChanged: (s) => setState(() => _p = _p.copyWith(genderCampusPref: s.first)),
      ),
      _label(context, 'Class timing', help: 'Leave empty for any.'),
      Wrap(spacing: 8, children: [
        for (final s in const ['morning', 'evening'])
          FilterChip(
            label: Text(shiftLabel(s)),
            selected: _p.shifts.contains(s),
            onSelected: (on) => setState(() => _p = _p.copyWith(shifts: _toggle(_p.shifts, s, on))),
          ),
      ]),
      SwitchListTile(
        contentPadding: EdgeInsets.zero,
        title: const Text('Only accredited programmes'),
        subtitle: const Text('For example PEC for engineering or PM&DC for medicine.'),
        value: _p.requireAccreditation,
        onChanged: (v) => setState(() => _p = _p.copyWith(requireAccreditation: v)),
      ),
      const SizedBox(height: 24),
      submitArea(widget.submitLabel,
          () => submit(() => ref.read(profileProvider.notifier).savePreferences(_p), widget.onDone)),
    ]);
  }
}

// ===================================================================== test scores

class TestScoresForm extends ConsumerStatefulWidget {
  const TestScoresForm({super.key, required this.profile, required this.reference});
  final Profile profile;
  final Reference reference;

  @override
  ConsumerState<TestScoresForm> createState() => _TestScoresFormState();
}

class _TestScoresFormState extends ConsumerState<TestScoresForm> with _Submitting {
  final _form = GlobalKey<FormState>();
  String? _test;
  final _score = TextEditingController();
  final _total = TextEditingController();
  final _year = TextEditingController(text: DateTime.now().year.toString());

  @override
  void dispose() {
    _score.dispose();
    _total.dispose();
    _year.dispose();
    super.dispose();
  }

  void _add() {
    if (_test == null) {
      setState(() => error = 'Please choose a test.');
      return;
    }
    if (!_form.currentState!.validate()) return;
    submit(
      () => ref.read(profileProvider.notifier).addTestScore({
        'test_code': _test,
        'year': int.parse(_year.text),
        'score': double.parse(_score.text),
        'total': double.parse(_total.text),
      }),
      () {
        _score.clear();
        _total.clear();
        setState(() => _test = null);
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final r = widget.reference;
    final scores = ref.watch(profileProvider).value?.testScores ?? widget.profile.testScores;
    return Form(
      key: _form,
      autovalidateMode: AutovalidateMode.onUserInteraction,
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        if (scores.isEmpty)
          const InfoBanner('No test scores yet. You can skip this and add them later.'),
        for (final s in scores)
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.assignment_turned_in_outlined),
            title: Text(r.testName(s.testCode)),
            subtitle: Text('${s.score.toStringAsFixed(0)} / ${s.total.toStringAsFixed(0)} '
                '(${percent(s.score / s.total * 100)}) · ${s.year}'),
            trailing: IconButton(
              tooltip: 'Remove',
              icon: const Icon(Icons.delete_outline),
              onPressed: () => ref.read(profileProvider.notifier).deleteTestScore(s.id),
            ),
          ),
        _label(context, 'Add a test score'),
        DropdownMenu<String>(
          key: ValueKey('test-${scores.length}'),
          initialSelection: _test,
          expandedInsets: EdgeInsets.zero,
          hintText: 'Choose test',
          dropdownMenuEntries: [for (final t in r.tests) DropdownMenuEntry(value: t.code, label: t.name)],
          onSelected: (v) => setState(() => _test = v),
        ),
        const SizedBox(height: 12),
        Row(children: [
          Expanded(
            child: TextFormField(
              controller: _score,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(labelText: 'Score'),
              validator: (v) => double.tryParse(v ?? '') == null ? 'Required' : null,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: TextFormField(
              controller: _total,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(labelText: 'Out of'),
              validator: (v) {
                final t = double.tryParse(v ?? '');
                if (t == null || t <= 0) return 'Required';
                final s = double.tryParse(_score.text);
                return s != null && s > t ? 'Less than score' : null;
              },
            ),
          ),
          const SizedBox(width: 12),
          SizedBox(
            width: 90,
            child: TextFormField(
              controller: _year,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Year'),
              validator: (v) => int.tryParse(v ?? '') == null ? 'Required' : null,
            ),
          ),
        ]),
        const SizedBox(height: 16),
        submitArea('Add score', _add),
      ]),
    );
  }
}
