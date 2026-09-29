import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config/app_config.dart';
import '../services/storage_service.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();

  factory ApiService() {
    return _instance;
  }

  ApiService._internal();

  // Get HTTP headers with JWT token
  Map<String, String> _getHeaders(String? token) {
    final headers = {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
    print('🔐 Headers being sent: $headers');
    print('🔐 Token value: $token');
    return headers;
  }

  // Generic GET request
  Future<dynamic> get(String endpoint, {String? token}) async {
    try {
      final url = Uri.parse('${AppConfig.baseUrl}$endpoint');
      print('📤 GET: $url');
      print('📤 Token passed: $token');
      final response = await http
          .get(url, headers: _getHeaders(token))
          .timeout(AppConfig.apiTimeout);
      print('📥 GET Response: ${response.statusCode}');
      return _handleResponse(response);
    } catch (e) {
      print('❌ GET Error: $e');
      throw _handleError(e);
    }
  }

  // Generic POST request
  Future<dynamic> post(
    String endpoint, {
    required Map<String, dynamic> body,
    String? token,
  }) async {
    try {
      final url = Uri.parse('${AppConfig.baseUrl}$endpoint');
      print('📤 POST: $url');
      print('📤 Token passed: $token');
      print('📤 Body: $body');
      final response = await http
          .post(
            url,
            headers: _getHeaders(token),
            body: jsonEncode(body),
          )
          .timeout(AppConfig.apiTimeout);
      print('📥 POST Response: ${response.statusCode}');
      return _handleResponse(response);
    } catch (e) {
      print('❌ POST Error: $e');
      throw _handleError(e);
    }
  }

  // Generic PUT request
  Future<dynamic> put(
    String endpoint, {
    required Map<String, dynamic> body,
    String? token,
  }) async {
    try {
      final url = Uri.parse('${AppConfig.baseUrl}$endpoint');
      print('📤 PUT: $url');
      print('📤 Token passed: $token');
      print('📤 Body: $body');
      final response = await http
          .put(
            url,
            headers: _getHeaders(token),
            body: jsonEncode(body),
          )
          .timeout(AppConfig.apiTimeout);
      print('📥 PUT Response: ${response.statusCode}');
      return _handleResponse(response);
    } catch (e) {
      print('❌ PUT Error: $e');
      throw _handleError(e);
    }
  }

  // Generic DELETE request
  Future<dynamic> delete(String endpoint, {String? token}) async {
    try {
      final url = Uri.parse('${AppConfig.baseUrl}$endpoint');
      print('📤 DELETE: $url');
      print('📤 Token passed: $token');
      final response = await http
          .delete(url, headers: _getHeaders(token))
          .timeout(AppConfig.apiTimeout);
      print('📥 DELETE Response: ${response.statusCode}');
      return _handleResponse(response);
    } catch (e) {
      print('❌ DELETE Error: $e');
      throw _handleError(e);
    }
  }

  // Handle response
  dynamic _handleResponse(http.Response response) {
    final statusCode = response.statusCode;
    final body = response.body;

    try {
      final jsonResponse = jsonDecode(body);

      if (statusCode >= 200 && statusCode < 300) {
        // Flask backend returns { "success": true, "data": { ... } }
        // For endpoints that don't have 'data' (like simple success messages),
        // we can just return the full response or null.
        if (jsonResponse is Map && jsonResponse.containsKey('data')) {
          return jsonResponse['data'];
        }
        return jsonResponse; // fallback for plain JSON
      } else if (statusCode == 401) {
        // Automatically handle unauthorized by clearing token
        StorageService().clearToken();
        throw ApiException('Unauthorized. Please login again.', statusCode);
      } else if (statusCode == 404) {
        throw ApiException(jsonResponse['message'] ?? 'Not found', statusCode);
      } else {
        final message = jsonResponse['message'] ?? 'API Error';
        throw ApiException(message, statusCode);
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Failed to parse response: $e', statusCode);
    }
  }

  // Handle errors
  String _handleError(dynamic error) {
    if (error is ApiException) {
      return error.message;
    }
    return 'Network error. Please check your connection.';
  }
}

class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, [this.statusCode]);

  @override
  String toString() => message;
}
