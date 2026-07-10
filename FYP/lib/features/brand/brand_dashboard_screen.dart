import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/api_client.dart';
import '../../core/providers/auth_notifier.dart';
import '../../core/theme.dart';
import '../../shared/widgets/ui.dart';

/// Fetches the calling brand's products so the dashboard can show real stats.
final brandProductsProvider =
    FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final response = await ApiClient().getMyProducts();
  return (response.data as List).cast<Map<String, dynamic>>();
});

class BrandDashboardScreen extends ConsumerWidget {
  const BrandDashboardScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 16,
        title: const Row(
          children: [
            AppLogo(size: 30),
            SizedBox(width: 10),
            Text('Brand Console'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_outline),
            onPressed: () => _showProfileMenu(context, ref),
            tooltip: 'Profile',
          ),
        ],
      ),
      body: AppBackground(
        child: SafeArea(
          top: false,
          child: RefreshIndicator(
            onRefresh: () async => ref.invalidate(brandProductsProvider),
            child: ListView(
              padding: const EdgeInsets.all(AppSpacing.md),
              children: [
                // Hero
                Container(
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  decoration: BoxDecoration(
                    gradient: AppColors.gradientPrimary,
                    borderRadius: BorderRadius.circular(AppRadius.xl),
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.primary.withOpacity(0.35),
                        blurRadius: 24,
                        offset: const Offset(0, 10),
                      ),
                    ],
                  ),
                  child: const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Welcome to your console',
                          style: TextStyle(
                              color: Colors.white,
                              fontSize: 20,
                              fontWeight: FontWeight.bold)),
                      SizedBox(height: 6),
                      Text(
                        'Manage your catalog, track stock, and reach shoppers.',
                        style: TextStyle(color: Colors.white70),
                      ),
                    ],
                  ),
                ).animate().fadeIn().moveY(begin: 16),

                const SizedBox(height: AppSpacing.lg),
                const SectionHeader(title: 'Quick actions'),
                const SizedBox(height: AppSpacing.md),
                GridView.count(
                  crossAxisCount: 2,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisSpacing: AppSpacing.md,
                  mainAxisSpacing: AppSpacing.md,
                  childAspectRatio: 1.35,
                  children: [
                    _action(context, Icons.add_circle_outline, 'Upload Product',
                        () => context.push('/brand/upload')),
                    _action(context, Icons.inventory_2_outlined, 'My Products',
                        () => context.push('/brand/products')),
                    _action(context, Icons.insights_outlined, 'Analytics',
                        () => context.push('/brand/analytics')),
                    _action(context, Icons.settings_outlined, 'Settings', () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Settings coming soon')),
                      );
                    }),
                  ],
                ),

                const SizedBox(height: AppSpacing.lg),
                SectionHeader(
                  title: 'Overview',
                  trailing: IconButton(
                    icon: const Icon(Icons.refresh),
                    onPressed: () => ref.invalidate(brandProductsProvider),
                    tooltip: 'Refresh',
                  ),
                ),
                const SizedBox(height: AppSpacing.md),
                _buildStats(context, ref),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _action(
      BuildContext context, IconData icon, String label, VoidCallback onTap) {
    return SurfaceCard(
      onTap: onTap,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(0.12),
              borderRadius: BorderRadius.circular(AppRadius.md),
            ),
            child: Icon(icon, color: AppColors.primaryLight),
          ),
          const SizedBox(height: 10),
          Text(label,
              textAlign: TextAlign.center,
              style: const TextStyle(
                  fontWeight: FontWeight.w600, fontSize: 13)),
        ],
      ),
    );
  }

  Widget _buildStats(BuildContext context, WidgetRef ref) {
    final async = ref.watch(brandProductsProvider);
    return async.when(
      loading: () => const SurfaceCard(
        child: SizedBox(height: 80, child: LoadingView()),
      ),
      error: (e, _) => const SurfaceCard(
        child: Text('Stats unavailable — is the backend running?'),
      ),
      data: (products) {
        var totalStock = 0, outOfStock = 0;
        for (final p in products) {
          final specs = (p['size_specs'] as List?) ?? [];
          var stock = 0;
          for (final s in specs) {
            stock += ((s as Map)['stock_quantity'] as int?) ?? 0;
          }
          totalStock += stock;
          if (stock == 0) outOfStock++;
        }
        final tiles = [
          _stat('Products', '${products.length}', Icons.inventory_2_outlined,
              AppColors.primary),
          _stat('In stock', '$totalStock', Icons.check_circle_outline,
              AppColors.success),
          _stat('Out of stock', '$outOfStock', Icons.remove_shopping_cart_outlined,
              AppColors.warning),
        ];
        return Row(
          children: [
            for (int i = 0; i < tiles.length; i++) ...[
              Expanded(
                child: tiles[i].animate().fadeIn(delay: (100 * i).ms).moveY(begin: 12),
              ),
              if (i < tiles.length - 1) const SizedBox(width: AppSpacing.sm),
            ]
          ],
        );
      },
    );
  }

  Widget _stat(String label, String value, IconData icon, Color color) {
    return SurfaceCard(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 8),
          Text(value,
              style: const TextStyle(
                  fontSize: 22, fontWeight: FontWeight.bold)),
          Text(label,
              style: const TextStyle(
                  fontSize: 11, color: AppColors.textSecondary)),
        ],
      ),
    );
  }

  void _showProfileMenu(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.logout),
              title: const Text('Logout'),
              onTap: () {
                Navigator.pop(context);
                ref.read(authProvider.notifier).signOut();
              },
            ),
          ],
        ),
      ),
    );
  }
}
