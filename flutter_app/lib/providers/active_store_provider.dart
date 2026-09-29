import 'package:flutter/material.dart';

class ActiveStoreProvider extends ChangeNotifier {
  int? _activeStoreId;
  String? _activeStoreName;
  bool _isOnboarded = false;

  int? get activeStoreId => _activeStoreId;
  String? get activeStoreName => _activeStoreName;
  bool get isOnboarded => _isOnboarded;

  void setActiveStore(int storeId, String storeName) {
    _activeStoreId = storeId;
    _activeStoreName = storeName;
    notifyListeners();
  }

  void setOnboarded(bool status) {
    _isOnboarded = status;
    notifyListeners();
  }

  void clearStore() {
    _activeStoreId = null;
    _activeStoreName = null;
    _isOnboarded = false;
    notifyListeners();
  }
}
