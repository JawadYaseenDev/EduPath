import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

typedef Json = Map<String, dynamic>;

const apiBaseUrl = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://localhost:8000');

/// Error message that can be shown to staff as-is.
class ApiException implements Exception {
  ApiException(this.message, [this.statusCode]);
  final String message;
  final int? statusCode;
  @override
  String toString() => message;
}

class TokenStore {
  static const _key = 'admin_token';
  final _storage = const FlutterSecureStorage();
  String? _cached;
  Future<String?> read() async => _cached ??= await _storage.read(key: _key);
  Future<void> write(String t) async {
    _cached = t;
    await _storage.write(key: _key, value: t);
  }

  Future<void> clear() async {
    _cached = null;
    await _storage.delete(key: _key);
  }
}

/// Thin JSON client for the admin API.
class Api {
  Api(this.tokens, {this.onUnauthorised})
    : _dio = Dio(BaseOptions(baseUrl: apiBaseUrl, contentType: 'application/json')) {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (o, h) async {
          final t = await tokens.read();
          if (t != null) o.headers['Authorization'] = 'Bearer $t';
          h.next(o);
        },
        onError: (e, h) {
          if (e.response?.statusCode == 401) onUnauthorised?.call();
          h.next(e);
        },
      ),
    );
  }

  final TokenStore tokens;
  final void Function()? onUnauthorised;
  final Dio _dio;

  Future<dynamic> get(String path, [Map<String, dynamic>? query]) =>
      _send(() => _dio.get(path, queryParameters: query));
  Future<dynamic> post(String path, [Object? body]) => _send(() => _dio.post(path, data: body));
  Future<dynamic> put(String path, Object? body) => _send(() => _dio.put(path, data: body));

  Future<dynamic> _send(Future<Response> Function() call) async {
    try {
      return (await call()).data;
    } on DioException catch (e) {
      final r = e.response;
      if (r == null) throw ApiException('Cannot reach the server. Is the backend running?');
      final d = r.data;
      final msg = d is Map && d['detail'] is String ? d['detail'] as String : 'Something went wrong (${r.statusCode}).';
      throw ApiException(msg, r.statusCode);
    }
  }
}
