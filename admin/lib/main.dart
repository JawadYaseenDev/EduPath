import 'package:flutter/semantics.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import 'screens/basic_screens.dart';
import 'screens/offering_screen.dart';
import 'screens/review_screen.dart';
import 'screens/university_screens.dart';
import 'state.dart';

void main() {
  // Build with --dart-define=ENABLE_SEMANTICS=true for automated browser testing.
  if (const bool.fromEnvironment('ENABLE_SEMANTICS')) {
    WidgetsFlutterBinding.ensureInitialized();
    SemanticsBinding.instance.ensureSemantics();
  }
  runApp(const ProviderScope(child: AdminApp()));
}

final _routerProvider = Provider<GoRouter>(
  (ref) => GoRouter(
    initialLocation: '/',
    refreshListenable: ref.watch(sessionListenableProvider),
    redirect: (context, state) {
      final session = ref.read(sessionProvider);
      final path = state.matchedLocation;
      final from = state.uri.queryParameters['from'];
      // While the saved session is checked, wait on /loading and remember the destination.
      if (session.isLoading) {
        return path == '/loading' ? null : '/loading?from=${Uri.encodeComponent(state.uri.toString())}';
      }
      final signedIn = session.value != null;
      if (path == '/loading') {
        if (!signedIn) return '/login${from == null ? '' : '?from=${Uri.encodeComponent(from)}'}';
        return from ?? '/';
      }
      final atLogin = path == '/login';
      if (!signedIn) return atLogin ? null : '/login?from=${Uri.encodeComponent(state.uri.toString())}';
      if (atLogin) return from ?? '/';
      final staff = session.value!;
      const superOnly = ['/audit', '/settings'];
      if (!staff.isSuperAdmin && superOnly.contains(state.matchedLocation)) return '/';
      return null;
    },
    routes: [
      GoRoute(
        path: '/loading',
        builder: (_, _) => const Scaffold(body: Center(child: CircularProgressIndicator())),
      ),
      GoRoute(path: '/login', builder: (_, _) => const LoginScreen()),
      ShellRoute(
        builder: (context, state, child) => _Shell(location: state.matchedLocation, child: child),
        routes: [
          GoRoute(path: '/', builder: (_, _) => const DashboardScreen()),
          GoRoute(path: '/universities', builder: (_, _) => const UniversitiesScreen()),
          GoRoute(
            path: '/universities/:id',
            builder: (_, s) => UniversityScreen(id: s.pathParameters['id']!),
          ),
          GoRoute(
            path: '/offerings/:id',
            builder: (_, s) => OfferingScreen(id: s.pathParameters['id']!),
          ),
          GoRoute(path: '/review', builder: (_, _) => const ReviewScreen()),
          GoRoute(path: '/reports', builder: (_, _) => const ReportsScreen()),
          GoRoute(path: '/audit', builder: (_, _) => const AuditScreen()),
          GoRoute(path: '/settings', builder: (_, _) => const SettingsScreen()),
        ],
      ),
    ],
  ),
);

class AdminApp extends ConsumerWidget {
  const AdminApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ThemeData theme(Brightness b) => ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0F6E56), brightness: b),
      useMaterial3: true,
      inputDecorationTheme: const InputDecorationTheme(border: OutlineInputBorder()),
    );
    return MaterialApp.router(
      title: 'EduRecommend Admin',
      debugShowCheckedModeBanner: false,
      theme: theme(Brightness.light),
      darkTheme: theme(Brightness.dark),
      routerConfig: ref.watch(_routerProvider),
    );
  }
}

class _Shell extends ConsumerWidget {
  const _Shell({required this.location, required this.child});
  final String location;
  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final staff = ref.watch(sessionProvider).value;
    final items = <(String, IconData, String)>[
      ('/', Icons.dashboard_outlined, 'Dashboard'),
      ('/universities', Icons.account_balance_outlined, 'Universities'),
      ('/review', Icons.rate_review_outlined, 'Review'),
      ('/reports', Icons.flag_outlined, 'Reports'),
      if (staff?.isSuperAdmin ?? false) ('/audit', Icons.history, 'History'),
      if (staff?.isSuperAdmin ?? false) ('/settings', Icons.settings_outlined, 'Settings'),
    ];
    int index = 0;
    for (var i = 0; i < items.length; i++) {
      final path = items[i].$1;
      if (path == '/' ? location == '/' : location.startsWith(path)) index = i;
    }
    if (location.startsWith('/offerings')) index = 1;
    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: index,
            labelType: NavigationRailLabelType.all,
            leading: Padding(
              padding: const EdgeInsets.symmetric(vertical: 12),
              child: Image.asset('assets/logo.png', height: 36, semanticLabel: 'EduRecommend logo'),
            ),
            trailing: Expanded(
              child: Align(
                alignment: Alignment.bottomCenter,
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Tooltip(
                        message: '${staff?.email}\n${staff?.roleLabel}',
                        child: const Icon(Icons.account_circle_outlined),
                      ),
                      const SizedBox(height: 4),
                      Text(staff?.roleLabel ?? '', style: Theme.of(context).textTheme.labelSmall),
                      IconButton(
                        tooltip: 'Sign out',
                        icon: const Icon(Icons.logout),
                        onPressed: () => ref.read(sessionProvider.notifier).signOut(),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            destinations: [
              for (final (_, icon, label) in items) NavigationRailDestination(icon: Icon(icon), label: Text(label)),
            ],
            onDestinationSelected: (i) => context.go(items[i].$1),
          ),
          const VerticalDivider(width: 1),
          Expanded(child: child),
        ],
      ),
    );
  }
}
