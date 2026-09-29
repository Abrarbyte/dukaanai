class AppConfig {
  // API Configuration - Updated for Windows/Desktop
  static const String baseUrl = 'http://localhost:5000';
  static const String apiVersion = '/api';

  // Timeout durations
  static const Duration apiTimeout = Duration(seconds: 30);

  // Auth Constants
  static const String loginEndpoint = '$apiVersion/auth/login';
  static const String signupEndpoint = '$apiVersion/auth/signup';
  static const String logoutEndpoint = '$apiVersion/auth/logout';

  // Local storage keys
  static const String tokenKey = 'auth_token';
  static const String userKey = 'user_data';
  static const String themeKey = 'app_theme';

  // App info
  static const String appName = 'Shop Manager';
  static const String appVersion = '1.0.0';

  // Feature flags
  static const bool useMockData = false; // Turned OFF for Production
}
