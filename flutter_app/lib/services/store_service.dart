import 'dart:convert';
import 'api_service.dart';

class StoreService {
  final ApiService _apiService = ApiService();

  Future<List<dynamic>> getUserStores({String? token}) async {
    try {
      final response = await _apiService.get('/api/stores', token: token);
      // The API returns { "stores": [...], "total": ... }
      // but ApiService _handleResponse extracts "data" mapping, so we get the map containing 'stores'.
      if (response is Map && response.containsKey('stores')) {
        return response['stores'];
      }
      if (response is List) {
        return response;
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  Future<Map<String, dynamic>?> getDashboard(int storeId, {String? token}) async {
    try {
      // Null check for storeId
      if (storeId <= 0) return null;

      final response = await _apiService.get('/api/stores/$storeId/dashboard', token: token);
      if (response is Map<String, dynamic>) {
        return response;
      }
      return null;
    } catch (e) {
      return null;
    }
  }
}
