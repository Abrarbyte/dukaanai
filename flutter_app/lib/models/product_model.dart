class Product {
  final int id;
  final String name;
  final String? description;
  final double price;
  final int quantity;
  final String? category;
  final String? imageUrl;
  final double? cost;
  final DateTime createdAt;
  final DateTime updatedAt;

  Product({
    required this.id,
    required this.name,
    this.description,
    required this.price,
    required this.quantity,
    this.category,
    this.imageUrl,
    this.cost,
    required this.createdAt,
    required this.updatedAt,
  });

  // Factory constructor from JSON
  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      description: json['description'],
      price: (json['selling_price'] ?? json['price'] ?? 0).toDouble(),
      quantity: (json['current_stock'] ?? json['quantity'] ?? 0).toInt(),
      category: json['category'],
      imageUrl: json['image_url'],
      cost: (json['purchase_price'] ?? json['cost']) != null
          ? (json['purchase_price'] ?? json['cost']).toDouble()
          : null,
      createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
      updatedAt: DateTime.tryParse(json['updated_at'] ?? '') ?? DateTime.now(),
    );
  }

  // Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'price': price,
      'quantity': quantity,
      'category': category,
      'image_url': imageUrl,
      'cost': cost,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  // Calculate profit
  double getProfit() {
    if (cost == null) return 0;
    return price - cost!;
  }

  // Copy with method
  Product copyWith({
    int? id,
    String? name,
    String? description,
    double? price,
    int? quantity,
    String? category,
    String? imageUrl,
    double? cost,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Product(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      price: price ?? this.price,
      quantity: quantity ?? this.quantity,
      category: category ?? this.category,
      imageUrl: imageUrl ?? this.imageUrl,
      cost: cost ?? this.cost,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}
