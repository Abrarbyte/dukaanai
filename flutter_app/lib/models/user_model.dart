class User {
  final int id;
  final String email;
  final String username;
  final String? name;
  final String? phone;
  final String? shopName;
  final String? profilePicture;
  final DateTime createdAt;

  User({
    required this.id,
    required this.email,
    required this.username,
    this.name,
    this.phone,
    this.shopName,
    this.profilePicture,
    required this.createdAt,
  });

  // Factory constructor to create from JSON
  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] ?? 0,
      email: json['email'] ?? '',
      username: json['name'] ?? json['username'] ?? '',
      name: json['name'],
      phone: json['phone'],
      shopName: json['shop_name'],
      profilePicture: json['profile_picture'],
      createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
    );
  }

  // Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'username': username,
      'name': name,
      'phone': phone,
      'shop_name': shopName,
      'profile_picture': profilePicture,
      'created_at': createdAt.toIso8601String(),
    };
  }

  // Copy with method
  User copyWith({
    int? id,
    String? email,
    String? username,
    String? name,
    String? phone,
    String? shopName,
    String? profilePicture,
    DateTime? createdAt,
  }) {
    return User(
      id: id ?? this.id,
      email: email ?? this.email,
      username: username ?? this.username,
      name: name ?? this.name,
      phone: phone ?? this.phone,
      shopName: shopName ?? this.shopName,
      profilePicture: profilePicture ?? this.profilePicture,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
