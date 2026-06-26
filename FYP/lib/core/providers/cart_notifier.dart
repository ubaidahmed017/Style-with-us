import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class CartItem {
  final String productId;
  final String productName;
  final double price;
  final String? sizeSpecId;
  final String? sizeLabel;
  int quantity;

  CartItem({
    required this.productId,
    required this.productName,
    required this.price,
    this.sizeSpecId,
    this.sizeLabel,
    this.quantity = 1,
  });

  Map<String, dynamic> toJson() => {
    'productId': productId,
    'productName': productName,
    'price': price,
    'sizeSpecId': sizeSpecId,
    'sizeLabel': sizeLabel,
    'quantity': quantity,
  };

  factory CartItem.fromJson(Map<String, dynamic> json) => CartItem(
    productId: json['productId'],
    productName: json['productName'],
    price: json['price'],
    sizeSpecId: json['sizeSpecId'],
    sizeLabel: json['sizeLabel'],
    quantity: json['quantity'] ?? 1,
  );

  double get subtotal => price * quantity;
}

class CartState {
  final List<CartItem> items;
  final double total;

  CartState({
    required this.items,
    required this.total,
  });

  factory CartState.empty() => CartState(items: [], total: 0);

  CartState copyWith({
    List<CartItem>? items,
    double? total,
  }) => CartState(
    items: items ?? this.items,
    total: total ?? this.total,
  );
}

class CartNotifier extends Notifier<CartState> {
  static const String _cartKey = 'shopping_cart';

  @override
  CartState build() {
    _loadCartFromStorage();
    return CartState.empty();
  }

  Future<void> _loadCartFromStorage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final cartJson = prefs.getString(_cartKey);
      if (cartJson != null) {
        final List<dynamic> decoded = jsonDecode(cartJson);
        final items = decoded
            .map((item) => CartItem.fromJson(item as Map<String, dynamic>))
            .toList();
        _updateState(items);
      }
    } catch (e) {
      // Handle error silently
    }
  }

  Future<void> _saveCartToStorage(List<CartItem> items) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final cartJson = jsonEncode(items.map((item) => item.toJson()).toList());
      await prefs.setString(_cartKey, cartJson);
    } catch (e) {
      // Handle error silently
    }
  }

  void addItem(
    String productId,
    String productName,
    double price, {
    String? sizeSpecId,
    String? sizeLabel,
  }) {
    final items = [...state.items];
    final existingIndex = items.indexWhere(
      (item) =>
          item.productId == productId &&
          item.sizeSpecId == sizeSpecId,
    );

    if (existingIndex >= 0) {
      items[existingIndex].quantity++;
    } else {
      items.add(CartItem(
        productId: productId,
        productName: productName,
        price: price,
        sizeSpecId: sizeSpecId,
        sizeLabel: sizeLabel,
      ));
    }

    _updateState(items);
  }

  void removeItem(String productId, String? sizeSpecId) {
    final items = state.items
        .where((item) =>
            !(item.productId == productId && item.sizeSpecId == sizeSpecId))
        .toList();
    _updateState(items);
  }

  void updateQuantity(String productId, String? sizeSpecId, int quantity) {
    if (quantity <= 0) {
      removeItem(productId, sizeSpecId);
      return;
    }

    final items = [...state.items];
    final index = items.indexWhere(
      (item) =>
          item.productId == productId &&
          item.sizeSpecId == sizeSpecId,
    );

    if (index >= 0) {
      items[index].quantity = quantity;
      _updateState(items);
    }
  }

  void clearCart() {
    _updateState([]);
  }

  void _updateState(List<CartItem> items) {
    final total = items.fold<double>(0, (sum, item) => sum + item.subtotal);
    state = CartState(items: items, total: total);
    _saveCartToStorage(items);
  }
}

final cartProvider = NotifierProvider<CartNotifier, CartState>(() {
  return CartNotifier();
});

final cartTotalProvider = Provider<double>((ref) {
  final cart = ref.watch(cartProvider);
  return cart.total;
});

final cartItemCountProvider = Provider<int>((ref) {
  final cart = ref.watch(cartProvider);
  return cart.items.length;
});
