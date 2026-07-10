import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../core/theme.dart';
import '../../core/providers/orders_notifier.dart';

class OrderHistoryScreen extends ConsumerWidget {
  const OrderHistoryScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final orders = ref.watch(ordersProvider);
    final isEmpty = orders.isEmpty;

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Orders'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/shopper'),
        ),
      ),
      body: isEmpty
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(
                      Icons.receipt_long_outlined,
                      size: 80,
                      color: AppColors.textMuted,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'No orders yet',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Any orders you place will appear here.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: () => context.go('/shopper'),
                      child: const Text('Start Shopping'),
                    ),
                  ],
                ),
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: orders.length,
              itemBuilder: (context, index) {
                final order = orders[index];
                return _OrderCard(order: order);
              },
            ),
    );
  }
}

class _OrderCard extends StatefulWidget {
  final OrderModel order;

  const _OrderCard({Key? key, required this.order}) : super(key: key);

  @override
  State<_OrderCard> createState() => _OrderCardState();
}

class _OrderCardState extends State<_OrderCard> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    final order = widget.order;
    final formattedDate = DateFormat('MMM dd, yyyy - hh:mm a').format(order.orderDate);

    Color statusColor;
    IconData statusIcon;

    switch (order.status.toLowerCase()) {
      case 'delivered':
        statusColor = AppColors.success;
        statusIcon = Icons.check_circle_outline;
        break;
      case 'shipped':
        statusColor = AppColors.info;
        statusIcon = Icons.local_shipping_outlined;
        break;
      default:
        statusColor = AppColors.warning;
        statusIcon = Icons.cached_rounded;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: Container(
          decoration: BoxDecoration(
            border: Border(
              left: BorderSide(color: statusColor, width: 6),
            ),
          ),
          child: Column(
            children: [
              // Main Card info
              InkWell(
                onTap: () {
                  setState(() {
                    _isExpanded = !_isExpanded;
                  });
                },
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Order #${order.orderId}',
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                formattedDate,
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            ],
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                            decoration: BoxDecoration(
                              color: statusColor.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Row(
                              children: [
                                Icon(statusIcon, color: statusColor, size: 16),
                                const SizedBox(width: 4),
                                Text(
                                  order.status,
                                  style: TextStyle(
                                    color: statusColor,
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const Divider(height: 24),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            '${order.items.length} ${order.items.length == 1 ? 'Item' : 'Items'}',
                            style: const TextStyle(color: AppColors.textSecondary),
                          ),
                          Row(
                            children: [
                              Text(
                                'Total: \$${order.total.toStringAsFixed(2)}',
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                  color: AppColors.accent,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Icon(
                                _isExpanded ? Icons.expand_less : Icons.expand_more,
                                color: AppColors.textMuted,
                              ),
                            ],
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),

              // Expanded Item Details
              if (_isExpanded) ...[
                Container(
                  color: AppColors.bgSurface.withOpacity(0.3),
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Items Ordered',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 12),
                      ListView.separated(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: order.items.length,
                        separatorBuilder: (context, index) => const Divider(height: 16),
                        itemBuilder: (context, index) {
                          final item = order.items[index];
                          return Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      item.productName,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w500,
                                        fontSize: 14,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    if (item.sizeLabel != null)
                                      Text(
                                        'Size: ${item.sizeLabel}  |  Qty: ${item.quantity}',
                                        style: Theme.of(context).textTheme.bodySmall,
                                      )
                                    else
                                      Text(
                                        'Qty: ${item.quantity}',
                                        style: Theme.of(context).textTheme.bodySmall,
                                      ),
                                  ],
                                ),
                              ),
                              Text(
                                '\$${item.subtotal.toStringAsFixed(2)}',
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                ),
                              ),
                            ],
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
