import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import 'features/auth/auth_screens.dart';
import 'features/explore/explore_screen.dart';
import 'features/explore/programme_screen.dart';
import 'features/home/home_screen.dart';
import 'features/profile/profile_screen.dart';
import 'features/profile/setup_wizard.dart';
import 'features/recommendations/results_screen.dart';
import 'features/shortlist/shortlist_screen.dart';
import 'state/providers.dart';

/// Routes anyone can open without an account (guest browsing).
const _public = ['/welcome', '/login', '/register', '/explore', '/programme', '/university'];

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/home',
    refreshListenable: ref.watch(authListenableProvider),
    redirect: (context, state) {
      final status = ref.read(authProvider).status;
      final path = state.matchedLocation;
      // While checking the saved login, remember where the user was going.
      final from = state.uri.queryParameters['from'];
      if (status == AuthStatus.unknown) {
        return path == '/splash' ? null : '/splash?from=${Uri.encodeComponent(state.uri.toString())}';
      }
      if (path == '/splash') {
        final target = from ?? '/home';
        final targetPath = Uri.parse(target).path;
        final targetPublic = _public.any((p) => targetPath == p || targetPath.startsWith('$p/'));
        if (status == AuthStatus.signedOut) return targetPublic ? target : '/welcome';
        return const ['/welcome', '/login', '/register'].contains(targetPath) ? '/home' : target;
      }
      final isPublic = _public.any((p) => path == p || path.startsWith('$p/'));
      if (status == AuthStatus.signedOut) {
        return isPublic ? null : '/welcome';
      }
      // Signed in: auth pages lead to the dashboard (FR-01).
      if (path == '/welcome' || path == '/login' || path == '/register') {
        return '/home';
      }
      return null;
    },
    routes: [
      GoRoute(path: '/splash', builder: (_, _) => const Scaffold(body: Center(child: CircularProgressIndicator()))),
      GoRoute(path: '/welcome', builder: (_, _) => const WelcomeScreen()),
      GoRoute(path: '/login', builder: (_, _) => const AuthScreen(register: false)),
      GoRoute(path: '/register', builder: (_, _) => const AuthScreen(register: true)),
      GoRoute(path: '/setup', builder: (_, _) => const SetupWizard()),
      GoRoute(path: '/results', builder: (_, _) => const ResultsScreen()),
      GoRoute(path: '/results/all', builder: (_, _) => const AllQualifyingScreen()),
      GoRoute(
          path: '/programme/:id',
          builder: (_, s) => ProgrammeScreen(offeringId: s.pathParameters['id']!)),
      GoRoute(
          path: '/university/:id',
          builder: (_, s) => UniversityScreen(universityId: s.pathParameters['id']!)),
      GoRoute(
          path: '/compare',
          builder: (_, s) => CompareScreen(offeringIds: (s.extra as List?)?.cast<String>() ?? const [])),
      GoRoute(
          path: '/edit/qualification/:level',
          builder: (_, s) => EditSectionScreen(section: 'qualification', level: s.pathParameters['level'])),
      GoRoute(
          path: '/edit/:section',
          builder: (_, s) => EditSectionScreen(section: s.pathParameters['section']!)),
      StatefulShellRoute.indexedStack(
        builder: (context, state, shell) => _Shell(shell),
        branches: [
          StatefulShellBranch(routes: [GoRoute(path: '/home', builder: (_, _) => const HomeScreen())]),
          StatefulShellBranch(routes: [GoRoute(path: '/explore', builder: (_, _) => const ExploreScreen())]),
          StatefulShellBranch(routes: [GoRoute(path: '/shortlist', builder: (_, _) => const ShortlistScreen())]),
          StatefulShellBranch(routes: [GoRoute(path: '/profile', builder: (_, _) => const ProfileScreen())]),
        ],
      ),
    ],
  );
});

class _Shell extends ConsumerWidget {
  const _Shell(this.shell);
  final StatefulNavigationShell shell;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final signedIn = ref.watch(authProvider).status == AuthStatus.signedIn;
    return Scaffold(
      body: shell,
      bottomNavigationBar: signedIn
          ? NavigationBar(
              selectedIndex: shell.currentIndex,
              onDestinationSelected: (i) => shell.goBranch(i, initialLocation: i == shell.currentIndex),
              destinations: const [
                NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Home'),
                NavigationDestination(icon: Icon(Icons.search), label: 'Explore'),
                NavigationDestination(
                    icon: Icon(Icons.bookmark_border), selectedIcon: Icon(Icons.bookmark), label: 'Shortlist'),
                NavigationDestination(
                    icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'Profile'),
              ],
            )
          : null,
    );
  }
}
