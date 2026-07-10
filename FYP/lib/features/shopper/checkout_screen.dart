import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/providers/cart_notifier.dart';
import '../../core/providers/orders_notifier.dart';
import '../../core/api_client.dart';
import '../../core/theme.dart';
import '../../shared/widgets/ui.dart';

class CheckoutScreen extends ConsumerStatefulWidget {
  const CheckoutScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends ConsumerState<CheckoutScreen> {
  bool _isProcessing = false;
  String? _errorMessage;

  Future<void> _handleCheckout() async {
    final cartState = ref.read(cartProvider);
    if (cartState.items.isEmpty) {
      setState(() => _errorMessage = 'Your cart is empty');
      return;
    }

    setState(() {
      _isProcessing = true;
      _errorMessage = null;
    });

    try {
      final apiClient = ApiClient();
      final items = cartState.items
          .map((item) => {
                'product_id': item.productId,
                'quantity': item.quantity,
                if (item.sizeSpecId != null) 'size_spec_id': item.sizeSpecId,
              })
          .toList();

      final response = await apiClient.createPaymentIntent(items);

      if (response.statusCode == 200 && mounted) {
        // Demo payment (no live Stripe): brief processing delay.
        await Future.delayed(const Duration(seconds: 2));

        final orderItems = cartState.items
            .map((item) => OrderItem(
                  productId: item.productId,
                  productName: item.productName,
                  price: item.price,
                  sizeLabel: item.sizeLabel,
                  quantity: item.quantity,
                ))
            .toList();
        ref.read(ordersProvider.notifier).addOrder(orderItems, cartState.total);
        ref.read(cartProvider.notifier).clearCart();

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Order placed successfully!')),
          );
          context.go('/shopper');
        }
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Checkout failed. Please try again.';
        _isProcessing = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final cartState = ref.watch(cartProvider);
    final subtotal = cartState.total;
    final tax = subtotal * 0.08;
    final total = subtotal + tax;

    return Scaffold(
      appBar: AppBar(title: const Text('Checkout')),
      body: AppBackground(
        child: cartState.items.isEmpty
            ? EmptyState(
                icon: Icons.shopping_cart_outlined,
                title: 'Your cart is empty',
                subtitle: 'Browse the catalog and add items to check out.',
                action: GradientButton(
                  label: 'Continue Shopping',
                  expand: false,
                  onPressed: () => context.go('/shopper'),
                ),
              )
            : Column(
                children: [
                  Expanded(
                    child: ListView(
                      padding: const EdgeInsets.all(AppSpacing.md),
                      children: [
                        const SectionHeader(title: 'Order summary'),
                        const SizedBox(height: AppSpacing.md),
                        SurfaceCard(
                          padding: EdgeInsets.zero,
                          child: Column(
                            children: [
                              for (int i = 0;
                                  i < cartState.items.length;
                                  i++) ...[
                                if (i > 0)
                                  Divider(height: 1, color: AppColors.border),
                                _item(cartState.items[i]),
                              ]
                            ],
                          ),
                        ).animate().fadeIn().moveY(begin: 12),
                        const SizedBox(height: AppSpacing.lg),
                        SurfaceCard(
                          child: Column(
                            children: [
                              _row('Subtotal',
                                  '\$${subtotal.toStringAsFixed(2)}'),
                              const SizedBox(height: 10),
                              _row('Shipping', 'FREE',
                                  valueColor: AppColors.success),
                              const SizedBox(height: 10),
                              _row('Tax (8%)', '\$${tax.toStringAsFixed(2)}'),
                              Divider(height: 24, color: AppColors.border),
                              _row('Total', '\$${total.toStringAsFixed(2)}',
                                  bold: true),
                            ],
                          ),
                        ).animate().fadeIn(delay: 100.ms).moveY(begin: 12),
                        if (_errorMessage != null) ...[
                          const SizedBox(height: AppSpacing.md),
                          AppErrorBanner(message: _errorMessage!),
                        ],
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.all(AppSpacing.md),
                    decoration: BoxDecoration(
                      color: AppColors.bgSurface,
                      border: Border(
                          top: BorderSide(color: AppColors.border)),
                    ),
                    child: SafeArea(
                      top: false,
                      child: GradientButton(
                        label: _isProcessing
                            ? 'Processing…'
                            : 'Place Order · \$${total.toStringAsFixed(2)}',
                        icon: Icons.lock_outline,
                        loading: _isProcessing,
                        onPressed: _isProcessing ? null : _handleCheckout,
                      ),
                    ),
                  ),
                ],
              ),
      ),
    );
  }

  Widget _item(CartItem item) {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(0.12),
              borderRadius: BorderRadius.circular(AppRadius.md),
            ),
            child: const Icon(Icons.checkroom, color: AppColors.primaryLight),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.productName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w600)),
                const SizedBox(height: 2),
                Text(
                  [
                    if (item.sizeLabel != null) 'Size ${item.sizeLabel}',
                    'Qty ${item.quantity}',
                  ].join('  ·  '),
                  style: const TextStyle(
                      fontSize: 12, color: AppColors.textSecondary),
                ),
              ],
            ),
          ),
          Text('\$${item.subtotal.toStringAsFixed(2)}',
              style: const TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _row(String label, String value,
      {bool bold = false, Color? valueColor}) {
    final style = TextStyle(
      fontSize: bold ? 18 : 14,
      fontWeight: bold ? FontWeight.bold : FontWeight.normal,
      color: valueColor ?? (bold ? AppColors.textPrimary : AppColors.textSecondary),
    );
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label,
            style: TextStyle(
                fontSize: bold ? 18 : 14,
                fontWeight: bold ? FontWeight.bold : FontWeight.normal)),
        Text(value, style: style),
      ],
    );
  }
}
