import './api_service.dart';
import '../models/product_model.dart';
import '../config/app_config.dart';

class ProductService {
  final ApiService _apiService = ApiService();

  // Mock products for development
  static final List<Map<String, dynamic>> mockProducts = [
    {
      'id': 1,
      'name': 'Wireless Headphones',
      'description': 'High-quality wireless headphones with noise cancellation',
      'price': 79.99,
      'quantity': 45,
      'category': 'Electronics',
      'image_url': null,
      'cost': 40.0,
      'created_at': '2024-01-01T10:00:00Z',
      'updated_at': '2024-01-01T10:00:00Z',
    },
    {
      'id': 2,
      'name': 'USB-C Cable',
      'description': 'Durable USB-C charging cable',
      'price': 12.99,
      'quantity': 120,
      'category': 'Accessories',
      'image_url': null,
      'cost': 5.0,
      'created_at': '2024-01-02T10:00:00Z',
      'updated_at': '2024-01-02T10:00:00Z',
    },
    {
      'id': 3,
      'name': 'Phone Case',
      'description': 'Protective phone case for all devices',
      'price': 19.99,
      'quantity': 85,
      'category': 'Accessories',
      'image_url': null,
      'cost': 8.0,
      'created_at': '2024-01-03T10:00:00Z',
      'updated_at': '2024-01-03T10:00:00Z',
    },
  ];

  // Get all products
  Future<List<Product>> getProducts(int storeId, {String? token}) async {
    try {
      final response = await _apiService.get('/api/stores/$storeId/products', token: token);

      List<Product> products = [];
      if (response is List) {
        products = response.map((p) => Product.fromJson(p)).toList();
      } else if (response is Map && response['products'] != null) {
        products = List<Product>.from(
          (response['products'] as List).map((p) => Product.fromJson(p)),
        );
      }

      return products;
    } catch (e) {
      throw ApiException(e.toString());
    }
  }

  // Get single product
  Future<Product> getProduct(int storeId, int id, {String? token}) async {
    try {
      final response = await _apiService.get('/api/stores/$storeId/products/$id', token: token);
      return Product.fromJson(response);
    } catch (e) {
      throw ApiException(e.toString());
    }
  }

  // Create product
  Future<Product> createProduct(
    int storeId,
    String name,
    double price, {
    String? description,
    int quantity = 0,
    String? category,
    double? cost,
    String? token,
  }) async {
    try {
      final response = await _apiService.post(
        '/api/stores/$storeId/products',
        body: {
          'name': name,
          'selling_price': price,
          'purchase_price': cost ?? 0.0,
          'current_stock': quantity,
          'description': description,
          'category': category,
        },
        token: token,
      );

      final prodJson = (response is Map && response.containsKey('product')) ? response['product'] : response;
      return Product.fromJson(prodJson);
    } catch (e) {
      throw ApiException(e.toString());
    }
  }

  // Update product
  Future<Product> updateProduct(
    int storeId,
    int id,
    String name,
    double price, {
    String? description,
    int? quantity,
    String? category,
    double? cost,
    String? token,
  }) async {
    try {
      final response = await _apiService.put(
        '/api/stores/$storeId/products/$id',
        body: {
          'name': name,
          'selling_price': price,
          'purchase_price': cost ?? 0.0,
          'current_stock': quantity ?? 0,
          'description': description,
          'category': category,
        },
        token: token,
      );

      final prodJson = (response is Map && response.containsKey('product')) ? response['product'] : response;
      return Product.fromJson(prodJson);
    } catch (e) {
      throw ApiException(e.toString());
    }
  }

  // Delete product
  Future<void> deleteProduct(int storeId, int id, {String? token}) async {
    try {
      await _apiService.delete('/api/stores/$storeId/products/$id', token: token);
    } catch (e) {
      throw ApiException(e.toString());
    }
  }
}
