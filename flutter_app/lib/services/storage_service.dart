import 'package:shared_preferences/shared_preferences.dart';
import '../config/app_config.dart';

class StorageService {
  static final StorageService _instance = StorageService._internal();
  static SharedPreferences? _prefs;

  factory StorageService() {
    return _instance;
  }

  StorageService._internal();

  // Initialize SharedPreferences
  Future<void> init() async {
    _prefs ??= await SharedPreferences.getInstance();
  }

  // Save token
  Future<bool> setToken(String token) async {
    await init();
    return await _prefs!.setString(AppConfig.tokenKey, token);
  }

  // Get token
  Future<String?> getToken() async {
    await init();
    return _prefs?.getString(AppConfig.tokenKey);
  }

  // Clear token
  Future<bool> clearToken() async {
    await init();
    return await _prefs!.remove(AppConfig.tokenKey);
  }

  // Save user data
  Future<bool> setUserData(String userData) async {
    await init();
    return await _prefs!.setString(AppConfig.userKey, userData);
  }

  // Get user data
  Future<String?> getUserData() async {
    await init();
    return _prefs?.getString(AppConfig.userKey);
  }

  // Clear user data
  Future<bool> clearUserData() async {
    await init();
    return await _prefs!.remove(AppConfig.userKey);
  }

  // Save theme preference
  Future<bool> setTheme(bool isDark) async {
    await init();
    return await _prefs!.setBool(AppConfig.themeKey, isDark);
  }

  // Get theme preference
  Future<bool> getTheme() async {
    await init();
    return _prefs?.getBool(AppConfig.themeKey) ?? false;
  }

  // Clear all data
  Future<bool> clearAll() async {
    await init();
    return await _prefs!.clear();
  }
}
