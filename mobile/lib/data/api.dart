import '../core/api_client.dart';
import 'models.dart';

/// All backend calls in one place.
class Api {
  Api(this._c);
  final ApiClient _c;

  // ---- auth (FR-01)
  Future<(String, AppUser)> register(String email, String password, String? name) async {
    final j = await _c.post('/v1/auth/register', {
      'email': email,
      'password': password,
      'full_name': name,
      'accept_terms': true,
    }) as Json;
    return (j['access_token'] as String, AppUser.fromJson(j['user'] as Json));
  }

  Future<(String, AppUser)> login(String email, String password) async {
    final j = await _c.post('/v1/auth/login', {'email': email, 'password': password}) as Json;
    return (j['access_token'] as String, AppUser.fromJson(j['user'] as Json));
  }

  Future<AppUser> me() async => AppUser.fromJson(await _c.get('/v1/auth/me') as Json);
  Future<void> logoutEverywhere() => _c.post('/v1/auth/logout-all');

  // ---- reference
  Future<Reference> reference() async => Reference.fromJson(await _c.get('/v1/reference') as Json);

  // ---- profile (FR-02)
  Future<Profile> profile() async => Profile.fromJson(await _c.get('/v1/profile') as Json);

  Future<Profile> updateProfile(Json body) async =>
      Profile.fromJson(await _c.put('/v1/profile', body) as Json);

  Future<Profile> saveQualification(Json body) async =>
      Profile.fromJson(await _c.put('/v1/profile/qualifications', body) as Json);

  Future<Profile> deleteQualification(String level) async =>
      Profile.fromJson(await _c.delete('/v1/profile/qualifications/$level') as Json);

  Future<Profile> addTestScore(Json body) async =>
      Profile.fromJson(await _c.post('/v1/profile/test-scores', body) as Json);

  Future<Profile> deleteTestScore(String id) async =>
      Profile.fromJson(await _c.delete('/v1/profile/test-scores/$id') as Json);

  Future<Profile> savePreferences(Preferences p) async =>
      Profile.fromJson(await _c.put('/v1/profile/preferences', p.toJson()) as Json);

  Future<Json> exportData() async => await _c.get('/v1/account/export') as Json;
  Future<void> deleteAccount() => _c.delete('/v1/account');

  // ---- recommendations (FR-04)
  Future<RecommendationRun> runRecommendations() async =>
      RecommendationRun.fromJson(await _c.post('/v1/recommendations/run') as Json);

  Future<RecommendationRun?> latestRecommendations() async {
    final j = await _c.get('/v1/recommendations/latest');
    return j == null ? null : RecommendationRun.fromJson(j as Json);
  }

  // ---- catalogue (FR-05)
  Future<List<OfferingCard>> searchProgrammes(Map<String, dynamic> query) async {
    final j = await _c.get('/v1/programmes', query: query) as Json;
    return (j['results'] as List).map((e) => OfferingCard.fromJson(e as Json)).toList();
  }

  Future<OfferingDetail> offering(String id) async =>
      OfferingDetail.fromJson(await _c.get('/v1/offerings/$id') as Json);

  Future<EligibilityCheck> myEligibility(String id) async =>
      EligibilityCheck.fromJson(await _c.get('/v1/offerings/$id/my-eligibility') as Json);

  Future<List<UniversitySummary>> universities() async => (await _c.get('/v1/universities') as List)
      .map((e) => UniversitySummary.fromJson(e as Json))
      .toList();

  Future<UniversityDetail> university(String id) async =>
      UniversityDetail.fromJson(await _c.get('/v1/universities/$id') as Json);

  Future<void> reportError(String entityType, String entityId, String message,
          {String? field}) =>
      _c.post('/v1/reports', {
        'entity_type': entityType,
        'entity_id': entityId,
        'field': field,
        'message': message,
      });

  // ---- shortlist (FR-06)
  Future<List<OfferingCard>> shortlist() async => _cards(await _c.get('/v1/shortlist'));
  Future<List<OfferingCard>> addToShortlist(String offeringId) async =>
      _cards(await _c.post('/v1/shortlist', {'offering_id': offeringId}));
  Future<List<OfferingCard>> removeFromShortlist(String offeringId) async =>
      _cards(await _c.delete('/v1/shortlist/$offeringId'));

  List<OfferingCard> _cards(dynamic j) =>
      (j as List).map((e) => OfferingCard.fromJson(e as Json)).toList();
}
