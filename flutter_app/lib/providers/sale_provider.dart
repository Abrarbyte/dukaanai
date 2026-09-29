import 'package:flutter/material.dart';
import '../models/sale_model.dart';

class SaleProvider extends ChangeNotifier {
  List<SaleItem> _cartItems = [];
  double _discount = 0;
  String? _paymentMethod;
  String? _notes;

  // Getters
  List<SaleItem> get cartItems => _cartItems;
  double get discount => _discount;
  String? get paymentMethod => _paymentMethod;
  String? get notes => _notes;

  // Calculate total
  double get totalAmount =>
      _cartItems.fold(0, (sum, item) => sum + item.totalPrice);

  double get finalAmount => totalAmount - _discount;

  // Add item to cart
  void addItem(SaleItem item) {
    // Check if item already exists
    final existingItem =
        _cartItems.where((i) => i.productId == item.productId).firstOrNull;

    if (existingItem != null) {
      // Update quantity
      final index = _cartItems.indexOf(existingItem);
      final updatedItem = SaleItem(
        productId: item.productId,
        productName: item.productName,
        quantity: existingItem.quantity + item.quantity,
        unitPrice: item.unitPrice,
        totalPrice: (existingItem.quantity + item.quantity) * item.unitPrice,
      );
      _cartItems[index] = updatedItem;
    } else {
      _cartItems.add(item);
    }

    notifyListeners();
  }

  // Remove item from cart
  void removeItem(int productId) {
    _cartItems.removeWhere((item) => item.productId == productId);
    notifyListeners();
  }

  // Update item quantity
  void updateItemQuantity(int productId, int quantity) {
    final item = _cartItems.firstWhere((i) => i.productId == productId);
    final index = _cartItems.indexOf(item);

    if (quantity <= 0) {
      removeItem(productId);
    } else {
      _cartItems[index] = SaleItem(
        productId: item.productId,
        productName: item.productName,
        quantity: quantity,
        unitPrice: item.unitPrice,
        totalPrice: quantity * item.unitPrice,
      );
      notifyListeners();
    }
  }

  // Set discount
  void setDiscount(double amount) {
    _discount = amount;
    notifyListeners();
  }

  // Set payment method
  void setPaymentMethod(String method) {
    _paymentMethod = method;
    notifyListeners();
  }

  // Set notes
  void setNotes(String? note) {
    _notes = note;
    notifyListeners();
  }

  // Clear cart
  void clearCart() {
    _cartItems.clear();
    _discount = 0;
    _paymentMethod = null;
    _notes = null;
    notifyListeners();
  }

  // Get sale object
  Sale getSale() {
    return Sale(
      id: 0, // Will be assigned by backend
      items: _cartItems,
      totalAmount: totalAmount,
      discountAmount: _discount > 0 ? _discount : null,
      finalAmount: finalAmount,
      paymentMethod: _paymentMethod,
      notes: _notes,
      createdAt: DateTime.now(),
    );
  }
}
