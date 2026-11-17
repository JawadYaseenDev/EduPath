import 'package:flutter/semantics.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import 'core/theme.dart';
import 'router.dart';

void main() {
  // Build with --dart-define=ENABLE_SEMANTICS=true to expose the accessibility tree on web
  // from the start (used for automated browser testing).
  if (const bool.fromEnvironment('ENABLE_SEMANTICS')) {
    WidgetsFlutterBinding.ensureInitialized();
    SemanticsBinding.instance.ensureSemantics();
  }
  runApp(const ProviderScope(child: UniRahApp()));
}

class UniRahApp extends ConsumerWidget {
  const UniRahApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp.router(
      title: 'UniRah',
      debugShowCheckedModeBanner: false,
      theme: buildTheme(Brightness.light),
      darkTheme: buildTheme(Brightness.dark),
      routerConfig: ref.watch(routerProvider),
    );
  }
}
