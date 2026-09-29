class Sale {
  final int id;
  final List<SaleItem> items;
  final double totalAmount;
  final double? discountAmount;
  final double finalAmount;
  final String? paymentMethod;
  final String? notes;
  final DateTime createdAt;

  Sale({
    required this.id,
    required this.items,
    required this.totalAmount,
    this.discountAmount,
    required this.finalAmount,
    this.paymentMethod,
    this.notes,
    required this.createdAt,
  });

  // Factory from JSON
  factory Sale.fromJson(Map<String, dynamic> json) {
    List<SaleItem> items = [];
    if (json['items'] != null) {
      items = List<SaleItem>.from(
        (json['items'] as List).map((item) => SaleItem.fromJson(item)),
      );
    }

    return Sale(
      id: json['id'] ?? 0,
      items: items,
      totalAmount: (json['total_amount'] ?? 0).toDouble(),
      discountAmount: json['discount_amount'] != null
          ? (json['discount_amount']).toDouble()
          : null,
      finalAmount: (json['final_amount'] ?? 0).toDouble(),
      paymentMethod: json['payment_method'],
      notes: json['notes'],
      createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
    );
  }

  // Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'items': items.map((item) => item.toJson()).toList(),
      'total_amount': totalAmount,
      'discount_amount': discountAmount,
      'final_amount': finalAmount,
      'payment_method': paymentMethod,
      'notes': notes,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

class SaleItem {
  final int productId;
  final String productName;
  final int quantity;
  final double unitPrice;
  final double totalPrice;

  SaleItem({
    required this.productId,
    required this.productName,
    required this.quantity,
    required this.unitPrice,
    required this.totalPrice,
  });

  // Factory from JSON
  factory SaleItem.fromJson(Map<String, dynamic> json) {
    return SaleItem(
      productId: json['product_id'] ?? 0,
      productName: json['product_name'] ?? '',
      quantity: json['quantity'] ?? 1,
      unitPrice: (json['unit_price'] ?? 0).toDouble(),
      totalPrice: (json['total_price'] ?? 0).toDouble(),
    );
  }

  // Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'product_id': productId,
      'product_name': productName,
      'quantity': quantity,
      'unit_price': unitPrice,
      'total_price': totalPrice,
    };
  }
}
