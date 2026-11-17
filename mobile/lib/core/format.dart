import 'package:intl/intl.dart';

final _pkr = NumberFormat.decimalPattern('en_PK');

String pkr(num? amount) => amount == null ? 'Not available' : 'PKR ${_pkr.format(amount)}';

String percent(num? value) {
  if (value == null) return '-';
  final text = value.toStringAsFixed(2);
  return '${text.replaceAll(RegExp(r'\.?0+$'), '')}%';
}

String niceDate(String? iso) {
  if (iso == null) return '-';
  final date = DateTime.tryParse(iso);
  return date == null ? iso : DateFormat('d MMM yyyy').format(date);
}

String sectorLabel(String? sector) => switch (sector) {
      'public' => 'Public',
      'private' => 'Private',
      'semi_government' => 'Semi-government',
      _ => sector ?? '-',
    };

String genderPolicyLabel(String? policy) => switch (policy) {
      'women_only' => 'Women only',
      'men_only' => 'Men only',
      _ => 'Co-education',
    };

String shiftLabel(String? shift) => switch (shift) {
      'evening' => 'Evening',
      'weekend' => 'Weekend',
      _ => 'Morning',
    };

String feeBasisLabel(String basis) => switch (basis) {
      'one_time' => 'one time',
      'per_semester' => 'per semester',
      'per_year' => 'per year',
      'per_credit_hour' => 'per credit hour',
      _ => basis,
    };

String titleCase(String code) => code
    .split('_')
    .where((p) => p.isNotEmpty)
    .map((p) => p[0].toUpperCase() + p.substring(1).toLowerCase())
    .join(' ');

String hostelLocationLabel(String location) => switch (location) {
      'on_campus' => 'On campus',
      'off_campus_university_managed' => 'Off campus (university managed)',
      'affiliated_private' => 'Private (affiliated)',
      _ => titleCase(location),
    };

String missLabel(String miss) => switch (miss) {
      'outside_location' => 'Outside your chosen locations',
      'over_budget' => 'Over your budget',
      'fee_unknown' => 'Fee not available',
      'sector' => 'Different university type',
      'no_hostel' => 'No suitable hostel',
      'hostel_unknown' => 'Hostel information not available',
      'campus_type' => 'Different campus type',
      'shift' => 'Different shift',
      'not_accredited' => 'Not accredited',
      'test_not_willing' => 'Needs a test you did not choose',
      _ => titleCase(miss),
    };
