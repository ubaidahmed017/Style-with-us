import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../shared/models/product_model.dart';
import '../../core/providers/auth_notifier.dart';
import '../../core/providers/recommendations_notifier.dart';
import '../../core/providers/profile_setup_notifier.dart';
import '../../core/providers/cart_notifier.dart';
import '../../core/providers/products_notifier.dart';

class ShopperHomeScreen extends ConsumerStatefulWidget {
  const ShopperHomeScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<ShopperHomeScreen> createState() => _ShopperHomeScreenState();
}

class _ShopperHomeScreenState extends ConsumerState<ShopperHomeScreen> {
  final _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Style With Us'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.favorite_border),
            onPressed: () => context.go('/shopper/wishlist'),
            tooltip: 'Wishlist',
          ),
          IconButton(
            icon: const Icon(Icons.shopping_cart_outlined),
            onPressed: () => context.go('/shopper/checkout'),
            tooltip: 'Cart',
          ),
          IconButton(
            icon: const Icon(Icons.person_outline),
            onPressed: () => _showProfileMenu(context, ref),
            tooltip: 'Profile',
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Section A: Recommended for You
            _buildRecommendedSection(context, ref),

            const SizedBox(height: 32),

            // Section B: Browse All
            _buildBrowseAllSection(context, ref),
          ],
        ),
      ),
    );
  }

  Widget _buildRecommendedSection(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(profileSetupProvider);
    final hasProfile = profile.gender != null;

    if (!hasProfile) {
      return Container(
        margin: const EdgeInsets.all(16),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.blue.shade50,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.blue.shade200),
        ),
        child: Row(
          children: [
            Icon(Icons.info, color: Colors.blue.shade700),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Complete Your Profile',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.blue.shade700,
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Set up your profile to get personalized recommendations',
                    style: TextStyle(fontSize: 13),
                  ),
                ],
              ),
            ),
            ElevatedButton(
              onPressed: () => context.go('/profile-setup'),
              child: const Text('Complete'),
            ),
          ],
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: Text(
            'Recommended for You',
            style: Theme.of(context).textTheme.titleLarge,
          ),
        ),
        _buildRecommendationsList(context, ref),
      ],
    );
  }

  Widget _buildRecommendationsList(BuildContext context, WidgetRef ref) {
    final recommendationsAsync = ref.watch(recommendationsProvider);

    return recommendationsAsync.when(
      data: (groups) {
        if (groups.isEmpty) {
          return Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 32),
            child: Center(
              child: Text(
                'No recommendations yet. Complete your profile!',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ),
          );
        }

        return Column(
          children: groups.map((group) {
            if (group.section == 'exact_match') {
              return _buildRecommendationGroup(
                context,
                title: 'Exact Match',
                subtitle: 'Color, size, and style for you',
                products: group.products,
                ref: ref,
              );
            } else if (group.section == 'similar_styles') {
              return _buildRecommendationGroup(
                context,
                title: 'Similar Styles',
                subtitle: 'Colors you\'ll love',
                products: group.products,
                ref: ref,
              );
            } else if (group.section == 'by_brand') {
              return _buildBrandGroup(
                context,
                brand: group.brand,
                products: group.products,
                ref: ref,
              );
            }
            return const SizedBox.shrink();
          }).toList(),
        );
      },
      loading: () => const Padding(
        padding: EdgeInsets.all(32),
        child: CircularProgressIndicator(),
      ),
      error: (error, stack) => Padding(
        padding: const EdgeInsets.all(16),
        child: Text('Error loading recommendations: $error'),
      ),
    );
  }

  Widget _buildRecommendationGroup(
    BuildContext context, {
    required String title,
    required String subtitle,
    required List<Product> products,
    required WidgetRef ref,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: Theme.of(context).textTheme.titleMedium),
              Text(subtitle,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.grey.shade600,
                )),
            ],
          ),
        ),
        SizedBox(
          height: 280,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: products.length,
            itemBuilder: (context, index) =>
                _buildProductCard(context, products[index], ref),
          ),
        ),
        const SizedBox(height: 16),
      ],
    );
  }

  Widget _buildBrandGroup(
    BuildContext context, {
    required Brand? brand,
    required List<Product> products,
    required WidgetRef ref,
  }) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade300),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                if (brand?.logoUrl != null)
                  Image.network(
                    brand!.logoUrl!,
                    width: 40,
                    height: 40,
                    errorBuilder: (_, __, ___) =>
                        const Icon(Icons.store, size: 40),
                  )
                else
                  const Icon(Icons.store, size: 40),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    brand?.companyName ?? 'Brand',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
              ],
            ),
          ),
          SizedBox(
            height: 220,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: products.length,
              itemBuilder: (context, index) =>
                  _buildProductCard(context, products[index], ref),
            ),
          ),
          const SizedBox(height: 12),
        ],
      ),
    );
  }

  Widget _buildProductCard(
    BuildContext context,
    Product product,
    WidgetRef ref,
  ) {
    return Card(
      margin: const EdgeInsets.only(right: 12),
      child: InkWell(
        onTap: () => context.go('/shopper/product/${product.productId}', extra: product),
        borderRadius: BorderRadius.circular(12),
        child: SizedBox(
          width: 150,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: ClipRRect(
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
                  child: Container(
                    width: double.infinity,
                    color: Colors.grey.shade900,
                    child: Image.network(
                      product.imageUrl,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) =>
                          const Icon(Icons.image_not_supported),
                    ),
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      product.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '\$${product.price.toStringAsFixed(2)}',
                      style: Theme.of(context).textTheme.labelMedium,
                    ),
                    const SizedBox(height: 8),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: () => context.go('/shopper/product/${product.productId}', extra: product),
                        icon: const Icon(Icons.info_outline, size: 16),
                        label: const Text('Details', style: TextStyle(fontSize: 11)),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildBrowseAllSection(BuildContext context, WidgetRef ref) {
    final productsAsync = ref.watch(productsProvider);
    final productsNotifier = ref.read(productsProvider.notifier);
    final currentFilter = productsNotifier.filter;

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Browse All',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 16),

          // Search Bar
          TextField(
            controller: _searchController,
            decoration: InputDecoration(
              hintText: 'Search products...',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: _searchController.text.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.clear),
                      onPressed: () {
                        _searchController.clear();
                        productsNotifier.setSearchFilter(null);
                      },
                    )
                  : null,
            ),
            onChanged: (val) {
              // Trigger search filter
              productsNotifier.setSearchFilter(val);
            },
          ),
          const SizedBox(height: 12),

          // Filters Row
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                ChoiceChip(
                  label: const Text('All'),
                  selected: currentFilter.gender == null,
                  onSelected: (selected) {
                    if (selected) productsNotifier.setGenderFilter(null);
                  },
                ),
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text('Men'),
                  selected: currentFilter.gender == 'male',
                  onSelected: (selected) {
                    if (selected) productsNotifier.setGenderFilter('male');
                  },
                ),
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text('Women'),
                  selected: currentFilter.gender == 'female',
                  onSelected: (selected) {
                    if (selected) productsNotifier.setGenderFilter('female');
                  },
                ),
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text('Unisex'),
                  selected: currentFilter.gender == 'unisex',
                  onSelected: (selected) {
                    if (selected) productsNotifier.setGenderFilter('unisex');
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Product Grid
          productsAsync.when(
            data: (products) {
              if (products.isEmpty) {
                return Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 32.0),
                    child: Column(
                      children: [
                        const Icon(Icons.search_off_rounded, size: 48, color: Colors.grey),
                        const SizedBox(height: 12),
                        const Text('No products match your filters.'),
                        const SizedBox(height: 12),
                        TextButton(
                          onPressed: () {
                            _searchController.clear();
                            productsNotifier.clearAllFilters();
                          },
                          child: const Text('Clear Filters'),
                        ),
                      ],
                    ),
                  ),
                );
              }

              return GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  childAspectRatio: 0.65,
                ),
                itemCount: products.length,
                itemBuilder: (context, index) {
                  final product = products[index];
                  return _buildBrowseProductCard(context, product, ref);
                },
              );
            },
            loading: () => const Center(
              child: Padding(
                padding: EdgeInsets.symmetric(vertical: 32.0),
                child: CircularProgressIndicator(),
              ),
            ),
            error: (err, stack) => Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 32.0),
                child: Text('Error: $err'),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBrowseProductCard(
    BuildContext context,
    Product product,
    WidgetRef ref,
  ) {
    return Card(
      child: InkWell(
        onTap: () => context.go('/shopper/product/${product.productId}', extra: product),
        borderRadius: BorderRadius.circular(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: ClipRRect(
                borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                child: Container(
                  width: double.infinity,
                  color: Colors.grey.shade900,
                  child: Image.network(
                    product.imageUrl,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) =>
                        const Center(child: Icon(Icons.image_not_supported)),
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '\$${product.price.toStringAsFixed(2)}',
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                          color: Colors.redAccent,
                        ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showProfileMenu(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ListTile(
            leading: const Icon(Icons.person),
            title: const Text('Edit Profile'),
            onTap: () {
              Navigator.pop(context);
              context.go('/profile-setup');
            },
          ),
          ListTile(
            leading: const Icon(Icons.receipt_long),
            title: const Text('My Orders'),
            onTap: () {
              Navigator.pop(context);
              context.go('/shopper/orders');
            },
          ),
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
    );
  }
}
