import 'package:flutter/material.dart';
import '../models/user_model.dart';
import '../services/auth_service.dart';
import '../services/storage_service.dart';

class AuthProvider extends ChangeNotifier {
  final AuthService _authService = AuthService();
  final StorageService _storageService = StorageService();

  User? _user;
  String? _token;
  bool _isLoading = false;
  String? _error;
  bool _isLoggedIn = false;

  // Getters
  User? get user => _user;
  String? get token => _token;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isLoggedIn => _isLoggedIn;

  // Constructor - check if already logged in
  AuthProvider() {
    _checkLoginStatus();
  }

  // Check if user is logged in
  Future<void> _checkLoginStatus() async {
    _token = await _storageService.getToken();
    _isLoggedIn = _token != null;
    print('🔑 Token loaded on startup: $_token');
    print('🔑 Is logged in: $_isLoggedIn');
    notifyListeners();
  }

  // Login
  Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      final result = await _authService.login(
        email: email,
        password: password,
      );

      _token = result['token'];
      _user = result['user'];
      _isLoggedIn = true;
      _isLoading = false;
      print('✅ Login success! Token: $_token');

      notifyListeners();
      return {'success': true, 'is_onboarded': result['is_onboarded']};
    } catch (e) {
      _isLoading = false;
      _error = e.toString();
      _isLoggedIn = false;
      print('❌ Login failed: $e');
      notifyListeners();
      return {'success': false};
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
      _isLoading = true;
      _error = null;
      notifyListeners();

      final result = await _authService.signup(
        email: email,
        username: username,
        password: password,
        shopName: shopName,
      );

      _token = result['token'];
      _user = result['user'];
      _isLoggedIn = true;
      _isLoading = false;
      print('✅ Signup success! Token: $_token');

      notifyListeners();
      return {'success': true, 'is_onboarded': false};
    } catch (e) {
      _isLoading = false;
      _error = e.toString();
      _isLoggedIn = false;
      print('❌ Signup failed: $e');
      notifyListeners();
      return {'success': false};
    }
  }

  // Logout
  Future<void> logout() async {
    try {
      _isLoading = true;
      notifyListeners();

      await _authService.logout();

      _token = null;
      _user = null;
      _isLoggedIn = false;
      _error = null;
      _isLoading = false;

      notifyListeners();
    } catch (e) {
      _isLoading = false;
      _error = e.toString();
      notifyListeners();
    }
  }

  // Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
