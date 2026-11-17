import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api.dart';

const staffRoles = {'super_admin', 'data_editor', 'data_verifier', 'support'};

final tokenStoreProvider = Provider((_) => TokenStore());

final apiProvider = Provider<Api>(
  (ref) => Api(ref.watch(tokenStoreProvider), onUnauthorised: () => ref.read(sessionProvider.notifier).signOut()),
);

class Staff {
  Staff(this.id, this.email, this.role);
  final String id;
  final String email;
  final String role;

  bool get canEdit => const {'super_admin', 'data_editor', 'data_verifier'}.contains(role);
  bool get canVerify => const {'super_admin', 'data_verifier'}.contains(role);
  bool get isSuperAdmin => role == 'super_admin';

  String get roleLabel => switch (role) {
    'super_admin' => 'Super admin',
    'data_editor' => 'Data editor',
    'data_verifier' => 'Data verifier',
    'support' => 'Support',
    _ => role,
  };
}

/// null = not signed in. AsyncLoading while restoring a saved session.
class SessionNotifier extends AsyncNotifier<Staff?> {
  @override
  Future<Staff?> build() async {
    if (await ref.read(tokenStoreProvider).read() == null) return null;
    try {
      return _staff(await ref.read(apiProvider).get('/v1/auth/me') as Json);
    } catch (_) {
      await ref.read(tokenStoreProvider).clear();
      return null;
    }
  }

  Staff _staff(Json j) {
    if (!staffRoles.contains(j['role'])) {
      throw ApiException('This account does not have access to the admin panel.');
    }
    return Staff(j['id'], j['email'], j['role']);
  }

  Future<void> signIn(String email, String password) async {
    final api = ref.read(apiProvider);
    final j = await api.post('/v1/auth/login', {'email': email, 'password': password}) as Json;
    final staff = _staff(j['user'] as Json); // throws for student accounts
    await ref.read(tokenStoreProvider).write(j['access_token'] as String);
    state = AsyncData(staff);
  }

  Future<void> signOut() async {
    await ref.read(tokenStoreProvider).clear();
    state = const AsyncData(null);
  }
}

final sessionProvider = AsyncNotifierProvider<SessionNotifier, Staff?>(SessionNotifier.new);

class SessionListenable extends ChangeNotifier {
  SessionListenable(Ref ref) {
    ref.listen(sessionProvider, (_, _) => notifyListeners());
  }
}

final sessionListenableProvider = Provider((ref) => SessionListenable(ref));

/// Lookup lists (cities, groups, subjects, tests...) from the public reference endpoint.
final referenceProvider = FutureProvider<Json>(
  (ref) async => await ref.watch(apiProvider).get('/v1/reference') as Json,
);

final sourcesProvider = FutureProvider<List<Json>>(
  (ref) async => ((await ref.watch(apiProvider).get('/v1/admin/sources')) as List).cast<Json>(),
);

/// Bumped after every write so screens reload.
final refreshProvider = NotifierProvider<RefreshNotifier, int>(RefreshNotifier.new);

class RefreshNotifier extends Notifier<int> {
  @override
  int build() => 0;
  void bump() => state++;
}
