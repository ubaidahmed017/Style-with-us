import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import 'package:uuid/uuid.dart';

class OrderItem {
  final String productId;
  final String productName;
  final double price;
  final String? sizeLabel;
  final int quantity;

  OrderItem({
    required this.productId,
    required this.productName,
    required this.price,
    this.sizeLabel,
    required this.quantity,
  });

  Map<String, dynamic> toJson() => {
        'productId': productId,
        'productName': productName,
        'price': price,
        'sizeLabel': sizeLabel,
        'quantity': quantity,
      };

  factory OrderItem.fromJson(Map<String, dynamic> json) => OrderItem(
        productId: json['productId'],
        productName: json['productName'],
        price: json['price'],
        sizeLabel: json['sizeLabel'],
        quantity: json['quantity'],
      );

  double get subtotal => price * quantity;
}

class OrderModel {
  final String orderId;
  final DateTime orderDate;
  final List<OrderItem> items;
  final double total;
  final String status; // "Processing", "Shipped", "Delivered"

  OrderModel({
    required this.orderId,
    required this.orderDate,
    required this.items,
    required this.total,
    required this.status,
  });

  Map<String, dynamic> toJson() => {
        'orderId': orderId,
        'orderDate': orderDate.toIso8601String(),
        'items': items.map((item) => item.toJson()).toList(),
        'total': total,
        'status': status,
      };

  factory OrderModel.fromJson(Map<String, dynamic> json) => OrderModel(
        orderId: json['orderId'],
        orderDate: DateTime.parse(json['orderDate']),
        items: (json['items'] as List)
            .map((item) => OrderItem.fromJson(item as Map<String, dynamic>))
            .toList(),
        total: json['total'].toDouble(),
        status: json['status'] ?? 'Processing',
      );
}

class OrdersNotifier extends Notifier<List<OrderModel>> {
  static const String _ordersKey = 'order_history';

  @override
  List<OrderModel> build() {
    _loadOrdersFromStorage();
    return [];
  }

  Future<void> _loadOrdersFromStorage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final ordersJson = prefs.getString(_ordersKey);
      if (ordersJson != null) {
        final List<dynamic> decoded = jsonDecode(ordersJson);
        final orders = decoded
            .map((order) => OrderModel.fromJson(order as Map<String, dynamic>))
            .toList();
        // Sort orders so newest are first
        orders.sort((a, b) => b.orderDate.compareTo(a.orderDate));
        state = orders;
      }
    } catch (e) {
      // Handle error silently
    }
  }

  Future<void> _saveOrdersToStorage(List<OrderModel> orders) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final ordersJson = jsonEncode(orders.map((order) => order.toJson()).toList());
      await prefs.setString(_ordersKey, ordersJson);
    } catch (e) {
      // Handle error silently
    }
  }

  void addOrder(List<OrderItem> items, double total) {
    final newOrder = OrderModel(
      orderId: const Uuid().v4().substring(0, 8).toUpperCase(),
      orderDate: DateTime.now(),
      items: items,
      total: total,
      status: 'Processing',
    );

    final updatedOrders = [newOrder, ...state];
    state = updatedOrders;
    _saveOrdersToStorage(updatedOrders);
  }
}

final ordersProvider = NotifierProvider<OrdersNotifier, List<OrderModel>>(() {
  return OrdersNotifier();
});
