import 'package:flutter/material.dart';
import '../models/product_model.dart';
import '../services/product_service.dart';

class ProductProvider extends ChangeNotifier {
  final ProductService _productService = ProductService();

  List<Product> _products = [];
  bool _isLoading = false;
  String? _error;

  // Getters
  List<Product> get products => _products;
  bool get isLoading => _isLoading;
  String? get error => _error;

  // Get all products
  Future<void> fetchProducts(int storeId, {String? token}) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      _products = await _productService.getProducts(storeId, token: token);
      _isLoading = false;

      notifyListeners();
    } catch (e) {
      _isLoading = false;
      _error = e.toString();
      notifyListeners();
    }
  }

  // Add product
  Future<bool> addProduct(
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
      _isLoading = true;
      _error = null;
      notifyListeners();

      final newProduct = await _productService.createProduct(
        storeId,
        name,
        price,
        description: description,
        quantity: quantity,
        category: category,
        cost: cost,
        token: token,
      );

      _products.add(newProduct);
      _isLoading = false;

      notifyListeners();
      return true;
    } catch (e) {
      _isLoading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  // Update product
  Future<bool> updateProduct(
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
      _isLoading = true;
      _error = null;
      notifyListeners();

      final updatedProduct = await _productService.updateProduct(
        storeId,
        id,
        name,
        price,
        description: description,
        quantity: quantity,
        category: category,
        cost: cost,
        token: token,
      );

      final index = _products.indexWhere((p) => p.id == id);
      if (index != -1) {
        _products[index] = updatedProduct;
      }

      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _isLoading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  // Delete product
  Future<bool> deleteProduct(int storeId, int id, {String? token}) async {
    try {
      _isLoading = true;
      _error = null;
      notifyListeners();

      await _productService.deleteProduct(storeId, id, token: token);

      _products.removeWhere((p) => p.id == id);
      _isLoading = false;

      notifyListeners();
      return true;
    } catch (e) {
      _isLoading = false;
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  // Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
