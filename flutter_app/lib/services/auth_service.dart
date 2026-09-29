import './api_service.dart';
import './storage_service.dart';
import '../models/user_model.dart';
import '../config/app_config.dart';

class AuthService {
  final ApiService _apiService = ApiService();
  final StorageService _storageService = StorageService();

  // Login
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _apiService.post(
        AppConfig.loginEndpoint,
        body: {'email': email, 'password': password},
      );

      final token = response['access_token'];
      final userData = response['user'];

      await _storageService.setToken(token);

      return {
        'success': true,
        'token': token,
        'user': User.fromJson(userData),
        'is_onboarded': response['is_onboarded'] ?? false,
      };
    } catch (e) {
      throw ApiException(e.toString());
    }
  }

  // Signup
  Future<Map<String, dynamic>> signup({
    required String email,
    required String username,
    required String password,
    required String shopName,
  }) async {
    try {
      final response = await _apiService.post(
        AppConfig.signupEndpoint,
        body: {
          'email': email,
          'name': username,
          'password': password,
        },
      );

      final token = response['access_token'];
      final userData = response['user'];

      await _storageService.setToken(token);

      return {
        'success': true,
        'token': token,
        'user': User.fromJson(userData),
        'is_onboarded': false,
      };
    } catch (e) {
      throw ApiException(e.toString());
    }
  }

  // Logout
  Future<void> logout() async {
    try {
      // Call backend logout
      try {
        await _apiService.post(AppConfig.logoutEndpoint, body: {});
      } catch (e) {
        // ignore backend logout crashes if token expired
      }
      await _storageService.clearToken();
    } catch (e) {
      throw ApiException('Logout failed');
    }
  }

  // Get stored token
  Future<String?> getToken() async {
    return await _storageService.getToken();
  }

  // Check if user is logged in
  Future<bool> isLoggedIn() async {
    final token = await _storageService.getToken();
    return token != null && token.isNotEmpty;
  }
}
