import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import 'token_storage.dart';

/// Base URL of the backend. Override with:
///   flutter run --dart-define=API_BASE_URL=https://api.example.com
String apiBaseUrl() {
  const fromEnv = String.fromEnvironment('API_BASE_URL');
  if (fromEnv.isNotEmpty) return fromEnv;
  if (kIsWeb) return 'http://localhost:8000';
  // Android emulator reaches the host computer at 10.0.2.2.
  if (defaultTargetPlatform == TargetPlatform.android) return 'http://10.0.2.2:8000';
  return 'http://localhost:8000';
}

/// An error with a message that can be shown to the student as-is.
class ApiException implements Exception {
  ApiException(this.message, {this.statusCode});
  final String message;
  final int? statusCode;

  bool get isUnauthorised => statusCode == 401;

  @override
  String toString() => message;
}

class ApiClient {
  ApiClient(this._tokens, {void Function()? onUnauthorised})
      : _dio = Dio(BaseOptions(
          baseUrl: apiBaseUrl(),
          connectTimeout: const Duration(seconds: 15),
          receiveTimeout: const Duration(seconds: 30),
          contentType: 'application/json',
        )) {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _tokens.read();
        if (token != null) options.headers['Authorization'] = 'Bearer $token';
        handler.next(options);
      },
      onError: (error, handler) {
        if (error.response?.statusCode == 401) onUnauthorised?.call();
        handler.next(error);
      },
    ));
  }

  final Dio _dio;
  final TokenStorage _tokens;

  Future<dynamic> get(String path, {Map<String, dynamic>? query}) =>
      _send(() => _dio.get(path, queryParameters: query));

  Future<dynamic> post(String path, [Object? body]) => _send(() => _dio.post(path, data: body));

  Future<dynamic> put(String path, Object? body) => _send(() => _dio.put(path, data: body));

  Future<dynamic> delete(String path) => _send(() => _dio.delete(path));

  Future<dynamic> _send(Future<Response> Function() call) async {
    try {
      final response = await call();
      return response.data;
    } on DioException catch (e) {
      throw _toApiException(e);
    }
  }

  ApiException _toApiException(DioException e) {
    final response = e.response;
    if (response == null) {
      return ApiException(
        'Could not connect. Please check your internet connection and try again.',
      );
    }
    final data = response.data;
    String message = 'Something went wrong. Please try again.';
    if (data is Map && data['detail'] is String) {
      message = data['detail'] as String;
    } else if (data is Map && data['detail'] is List && (data['detail'] as List).isNotEmpty) {
      message = ((data['detail'] as List).first as Map)['msg']?.toString() ?? message;
    }
    return ApiException(message, statusCode: response.statusCode);
  }
}
