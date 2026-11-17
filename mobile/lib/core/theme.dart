import 'package:material_ui/material_ui.dart';

const _seed = Color(0xFF0F6E56); // calm green

ThemeData buildTheme(Brightness brightness) {
  final scheme = ColorScheme.fromSeed(seedColor: _seed, brightness: brightness);
  return ThemeData(
    colorScheme: scheme,
    useMaterial3: true,
    visualDensity: VisualDensity.standard,
    inputDecorationTheme: const InputDecorationTheme(border: OutlineInputBorder()),
    cardTheme: CardThemeData(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: scheme.outlineVariant),
      ),
      margin: EdgeInsets.zero,
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(minimumSize: const Size(64, 48)),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(minimumSize: const Size(64, 48)),
    ),
  );
}

/// Eligibility colours. Always shown together with an icon and a word,
/// never colour alone (accessibility).
class StatusColors {
  static Color eligible(ColorScheme s) =>
      s.brightness == Brightness.dark ? const Color(0xFF7BD8A9) : const Color(0xFF1B7F4B);
  static Color potentially(ColorScheme s) =>
      s.brightness == Brightness.dark ? const Color(0xFFF5C26B) : const Color(0xFF9A6200);
  static Color notEligible(ColorScheme s) =>
      s.brightness == Brightness.dark ? const Color(0xFFF2A49B) : const Color(0xFFA63A2E);
}
