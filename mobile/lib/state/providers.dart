import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api_client.dart';
import '../core/token_storage.dart';
import '../data/api.dart';
import '../data/models.dart';

final tokenStorageProvider = Provider((_) => TokenStorage());

final apiProvider = Provider<Api>((ref) {
  final client = ApiClient(
    ref.watch(tokenStorageProvider),
    onUnauthorised: () => ref.read(authProvider.notifier).sessionExpired(),
  );
  return Api(client);
});

// ------------------------------------------------------------------ auth (FR-01)

enum AuthStatus { unknown, signedOut, signedIn }

class AuthState {
  const AuthState(this.status, [this.user]);
  final AuthStatus status;
  final AppUser? user;
}

class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() {
    _restore();
    return const AuthState(AuthStatus.unknown);
  }

  Future<void> _restore() async {
    final token = await ref.read(tokenStorageProvider).read();
    if (token == null) {
      state = const AuthState(AuthStatus.signedOut);
      return;
    }
    try {
      final user = await ref.read(apiProvider).me();
      state = AuthState(AuthStatus.signedIn, user);
    } catch (_) {
      await ref.read(tokenStorageProvider).clear();
      state = const AuthState(AuthStatus.signedOut);
    }
  }

  Future<void> login(String email, String password) async {
    final (token, user) = await ref.read(apiProvider).login(email, password);
    await _signedIn(token, user);
  }

  Future<void> register(String email, String password, String? name) async {
    final (token, user) = await ref.read(apiProvider).register(email, password, name);
    await _signedIn(token, user);
  }

  Future<void> _signedIn(String token, AppUser user) async {
    await ref.read(tokenStorageProvider).write(token);
    _clearUserData();
    state = AuthState(AuthStatus.signedIn, user);
  }

  /// Clears the session on this device (FR-01: "clear the active session on logout").
  Future<void> logout() async {
    await ref.read(tokenStorageProvider).clear();
    _clearUserData();
    state = const AuthState(AuthStatus.signedOut);
  }

  void sessionExpired() {
    if (state.status == AuthStatus.signedIn) logout();
  }

  void _clearUserData() {
    ref.invalidate(profileProvider);
    ref.invalidate(recommendationsProvider);
    ref.invalidate(shortlistProvider);
  }
}

final authProvider = NotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

/// Lets go_router re-check redirects whenever auth changes.
class AuthListenable extends ChangeNotifier {
  AuthListenable(Ref ref) {
    ref.listen(authProvider, (_, _) => notifyListeners());
  }
}

final authListenableProvider = Provider((ref) => AuthListenable(ref));

// ------------------------------------------------------------------ reference

final referenceProvider = FutureProvider<Reference>((ref) => ref.watch(apiProvider).reference());

// ------------------------------------------------------------------ profile (FR-02)

class ProfileNotifier extends AsyncNotifier<Profile> {
  @override
  Future<Profile> build() => ref.watch(apiProvider).profile();

  Future<void> _apply(Future<Profile> Function(Api api) action) async {
    final profile = await action(ref.read(apiProvider));
    state = AsyncData(profile);
  }

  Future<void> updatePersonal(Json body) => _apply((a) => a.updateProfile(body));
  Future<void> saveQualification(Json body) => _apply((a) => a.saveQualification(body));
  Future<void> deleteQualification(String level) => _apply((a) => a.deleteQualification(level));
  Future<void> addTestScore(Json body) => _apply((a) => a.addTestScore(body));
  Future<void> deleteTestScore(String id) => _apply((a) => a.deleteTestScore(id));
  Future<void> savePreferences(Preferences p) => _apply((a) => a.savePreferences(p));
}

final profileProvider = AsyncNotifierProvider<ProfileNotifier, Profile>(ProfileNotifier.new);

// ------------------------------------------------------------------ recommendations (FR-04)

class RecommendationsNotifier extends AsyncNotifier<RecommendationRun?> {
  @override
  Future<RecommendationRun?> build() => ref.watch(apiProvider).latestRecommendations();

  Future<void> run() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => ref.read(apiProvider).runRecommendations());
  }
}

final recommendationsProvider =
    AsyncNotifierProvider<RecommendationsNotifier, RecommendationRun?>(RecommendationsNotifier.new);

// ------------------------------------------------------------------ shortlist (FR-06)

class ShortlistNotifier extends AsyncNotifier<List<OfferingCard>> {
  @override
  Future<List<OfferingCard>> build() => ref.watch(apiProvider).shortlist();

  bool contains(String offeringId) =>
      state.value?.any((c) => c.offeringId == offeringId) ?? false;

  Future<void> toggle(String offeringId) async {
    final api = ref.read(apiProvider);
    final list = contains(offeringId)
        ? await api.removeFromShortlist(offeringId)
        : await api.addToShortlist(offeringId);
    state = AsyncData(list);
  }
}

final shortlistProvider =
    AsyncNotifierProvider<ShortlistNotifier, List<OfferingCard>>(ShortlistNotifier.new);

// ------------------------------------------------------------------ catalogue (FR-05)

final offeringProvider =
    FutureProvider.family<OfferingDetail, String>((ref, id) => ref.watch(apiProvider).offering(id));

final universityProvider = FutureProvider.family<UniversityDetail, String>(
    (ref, id) => ref.watch(apiProvider).university(id));
