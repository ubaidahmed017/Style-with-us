import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme.dart';
import '../../core/providers/profile_setup_notifier.dart';
import '../../core/providers/cart_notifier.dart';
import '../../core/providers/wishlist_notifier.dart';
import '../../shared/models/product_model.dart';

class ProductDetailScreen extends ConsumerStatefulWidget {
  final String productId;
  final Product? product;

  const ProductDetailScreen({
    Key? key,
    required this.productId,
    this.product,
  }) : super(key: key);

  @override
  ConsumerState<ProductDetailScreen> createState() => _ProductDetailScreenState();
}

class _ProductDetailScreenState extends ConsumerState<ProductDetailScreen> {
  Product? _product;
  ProductSizeSpec? _selectedSizeSpec;
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    if (widget.product != null) {
      _product = widget.product;
      _recommendAndSelectSize();
    } else {
      _fetchProductDetails();
    }
  }

  Future<void> _fetchProductDetails() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // In a real app, you would fetch from the backend API.
      // For now, we simulate fetching, or look for it in cached recommendations.
      await Future.delayed(const Duration(milliseconds: 500));

      // If not passed, use a mock fallback product
      if (mounted) {
        setState(() {
          _product = Product(
            productId: widget.productId,
            brandId: 'brand-1',
            sku: 'MOCK-PROD-${widget.productId.toUpperCase()}',
            name: 'Premium Slim Fit Blazer',
            description: 'Elevate your wardrobe with this premium slim-fit blazer. Crafted from high-quality stretch blend fabric, it offers both structure and comfort. Featuring classic notch lapels, a two-button closure, and functional pockets, it is perfect for both smart-casual and formal occasions.',
            price: 149.99,
            imageUrl: 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=600&auto=format&fit=crop&q=80',
            genderTarget: 'male',
            dominantColorHex: '#1D3557',
            sizeSpecs: [
              ProductSizeSpec(
                specId: 'spec-s',
                sizeLabel: 'S',
                stockQuantity: 10,
                chestMin: 85,
                chestMax: 93,
                waistMin: 70,
                waistMax: 78,
              ),
              ProductSizeSpec(
                specId: 'spec-m',
                sizeLabel: 'M',
                stockQuantity: 15,
                chestMin: 93,
                chestMax: 101,
                waistMin: 78,
                waistMax: 86,
              ),
              ProductSizeSpec(
                specId: 'spec-l',
                sizeLabel: 'L',
                stockQuantity: 8,
                chestMin: 101,
                chestMax: 109,
                waistMin: 86,
                waistMax: 94,
              ),
              ProductSizeSpec(
                specId: 'spec-xl',
                sizeLabel: 'XL',
                stockQuantity: 4,
                chestMin: 109,
                chestMax: 117,
                waistMin: 94,
                waistMax: 102,
              ),
            ],
          );
          _recommendAndSelectSize();
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = 'Failed to load product: $e';
          _isLoading = false;
        });
      }
    }
  }

  void _recommendAndSelectSize() {
    if (_product == null) return;

    final profile = ref.read(profileSetupProvider);
    if (profile.gender != null) {
      // Find matching size based on user measurements
      final recommendedSpec = _product!.findMatchingSize(
        chest: profile.chest,
        waist: profile.waist,
        hips: profile.hips,
        inseam: profile.inseam,
      );
      if (recommendedSpec != null) {
        _selectedSizeSpec = recommendedSpec;
        return;
      }
    }

    // Default fallback to first available stock
    if (_product!.sizeSpecs.isNotEmpty) {
      _selectedSizeSpec = _product!.sizeSpecs.firstWhere(
        (spec) => spec.stockQuantity > 0,
        orElse: () => _product!.sizeSpecs.first,
      );
    }
  }

  void _handleAddToCart() {
    if (_product == null || _selectedSizeSpec == null) return;

    ref.read(cartProvider.notifier).addItem(
      _product!.productId,
      _product!.name,
      _product!.price,
      sizeSpecId: _selectedSizeSpec!.specId,
      sizeLabel: _selectedSizeSpec!.sizeLabel,
    );

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Added ${_product!.name} (${_selectedSizeSpec!.sizeLabel}) to cart!'),
        backgroundColor: AppColors.success,
        action: SnackBarAction(
          label: 'Checkout',
          textColor: Colors.white,
          onPressed: () => context.go('/shopper/checkout'),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_errorMessage != null || _product == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Product Details')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 64, color: AppColors.error),
                const SizedBox(height: 16),
                Text(
                  _errorMessage ?? 'Product not found',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: _fetchProductDetails,
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    final product = _product!;
    final profile = ref.watch(profileSetupProvider);
    final hasProfile = profile.gender != null;
    final isFavorite = ref.watch(wishlistProvider).any((item) => item.productId == product.productId);

    // Find matching size based on user measurements (for recommendation banner)
    ProductSizeSpec? recommendedSpec;
    if (hasProfile) {
      recommendedSpec = product.findMatchingSize(
        chest: profile.chest,
        waist: profile.waist,
        hips: profile.hips,
        inseam: profile.inseam,
      );
    }

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          // Collapsible AppBar with Image
          SliverAppBar(
            expandedHeight: 400,
            pinned: true,
            leading: CircleAvatar(
              backgroundColor: Colors.black38,
              child: IconButton(
                icon: const Icon(Icons.arrow_back, color: Colors.white),
                onPressed: () => Navigator.of(context).pop(),
              ),
            ),
            actions: [
              CircleAvatar(
                backgroundColor: Colors.black38,
                child: IconButton(
                  icon: Icon(
                    isFavorite ? Icons.favorite : Icons.favorite_border,
                    color: isFavorite ? AppColors.accent : Colors.white,
                  ),
                  onPressed: () {
                    ref.read(wishlistProvider.notifier).toggleProduct(product);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(
                          isFavorite
                              ? 'Removed from wishlist'
                              : 'Added to wishlist',
                        ),
                        duration: const Duration(seconds: 1),
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(width: 8),
              CircleAvatar(
                backgroundColor: Colors.black38,
                child: IconButton(
                  icon: const Icon(Icons.shopping_cart_outlined, color: Colors.white),
                  onPressed: () => context.go('/shopper/checkout'),
                ),
              ),
              const SizedBox(width: 12),
            ],
            flexibleSpace: FlexibleSpaceBar(
              background: Hero(
                tag: 'product-image-${product.productId}',
                child: Image.network(
                  product.imageUrl,
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) => Container(
                    color: AppColors.bgSurface,
                    child: const Icon(Icons.image_not_supported, size: 80),
                  ),
                ),
              ),
            ),
          ),

          // Product Details Content
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Title, Brand & Price
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              product.name,
                              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'By Brand Console', // Placeholder or brand metadata
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    color: AppColors.primaryLight,
                                    fontWeight: FontWeight.w500,
                                  ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        '\$${product.price.toStringAsFixed(2)}',
                        style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                              color: AppColors.accent,
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // Recommended Size Alert Banner
                  if (hasProfile && recommendedSpec != null)
                    Container(
                      margin: const EdgeInsets.only(bottom: 24),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      decoration: BoxDecoration(
                        color: AppColors.success.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.success.withOpacity(0.3)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.check_circle_outline, color: AppColors.success, size: 24),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'AI Fit Recommendation',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: AppColors.success,
                                    fontSize: 14,
                                  ),
                                ),
                                Text(
                                  'Size ${recommendedSpec.sizeLabel} is your perfect fit based on your body profile.',
                                  style: const TextStyle(
                                    color: AppColors.textPrimary,
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    )
                  else if (hasProfile && recommendedSpec == null)
                    Container(
                      margin: const EdgeInsets.only(bottom: 24),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      decoration: BoxDecoration(
                        color: AppColors.warning.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.warning.withOpacity(0.3)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.warning_amber_rounded, color: AppColors.warning, size: 24),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Fit Advisory',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: AppColors.warning,
                                    fontSize: 14,
                                  ),
                                ),
                                const Text(
                                  'No standard size fits your exact measurements. Check the size details below.',
                                  style: TextStyle(
                                    color: AppColors.textPrimary,
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),

                  // Virtual Try-on Callout Section
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      gradient: AppColors.gradientPrimary,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Want to see how it looks?',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                  color: Colors.white,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                'Try this garment on your photo or in real-time AR!',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.white.withOpacity(0.9),
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 8),
                        Column(
                          children: [
                            ElevatedButton.icon(
                              onPressed: () => context.go('/shopper/try-on', extra: product),
                              icon: const Icon(Icons.photo_library_outlined, size: 16),
                              label: const Text('Try-On Photo', style: TextStyle(fontSize: 12)),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.white,
                                foregroundColor: AppColors.primary,
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                              ),
                            ),
                            const SizedBox(height: 8),
                            ElevatedButton.icon(
                              onPressed: () => context.go('/shopper/ar-tryon'),
                              icon: const Icon(Icons.camera_alt_outlined, size: 16),
                              label: const Text('Live AR', style: TextStyle(fontSize: 12)),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.black54,
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Description
                  Text(
                    'Description',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    product.description ?? 'No description available for this product.',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          height: 1.5,
                        ),
                  ),
                  const SizedBox(height: 24),

                  // Size Selector Title
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Select Size',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      if (recommendedSpec != null)
                        Text(
                          'Size ${recommendedSpec.sizeLabel} Recommended',
                          style: const TextStyle(
                            color: AppColors.success,
                            fontWeight: FontWeight.w600,
                            fontSize: 12,
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // Size selection chips
                  Wrap(
                    spacing: 12,
                    children: product.sizeSpecs.map((spec) {
                      final isSelected = _selectedSizeSpec?.specId == spec.specId;
                      final isOutOfStock = spec.stockQuantity <= 0;
                      final isRecommended = recommendedSpec?.specId == spec.specId;

                      return ChoiceChip(
                        label: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(spec.sizeLabel),
                              if (isRecommended) ...[
                                const SizedBox(width: 4),
                                const Icon(Icons.star, size: 12, color: Colors.amber),
                              ]
                            ],
                          ),
                        ),
                        selected: isSelected,
                        onSelected: isOutOfStock
                            ? null
                            : (selected) {
                                if (selected) {
                                  setState(() => _selectedSizeSpec = spec);
                                }
                              },
                        backgroundColor: AppColors.bgElevated,
                        selectedColor: AppColors.primary,
                        disabledColor: AppColors.bgDark.withOpacity(0.5),
                        labelStyle: TextStyle(
                          color: isSelected
                              ? Colors.white
                              : isOutOfStock
                                  ? AppColors.textMuted
                                  : AppColors.textPrimary,
                          fontWeight: isSelected || isRecommended ? FontWeight.bold : FontWeight.normal,
                        ),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 16),

                  // Selected size detail table
                  if (_selectedSizeSpec != null) ...[
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.bgSurface,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.textMuted.withOpacity(0.1)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                'Size Detail: ${_selectedSizeSpec!.sizeLabel}',
                                style: const TextStyle(fontWeight: FontWeight.bold),
                              ),
                              Text(
                                'Stock: ${_selectedSizeSpec!.stockQuantity} units available',
                                style: TextStyle(
                                  color: _selectedSizeSpec!.stockQuantity < 5
                                      ? AppColors.accent
                                      : AppColors.textSecondary,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                          const Divider(height: 16),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceAround,
                            children: [
                              if (_selectedSizeSpec!.chestMin != null)
                                _buildSpecMeasurement(
                                    'Chest',
                                    '${_selectedSizeSpec!.chestMin}-${_selectedSizeSpec!.chestMax} cm',
                                    profile.chest),
                              if (_selectedSizeSpec!.waistMin != null)
                                _buildSpecMeasurement(
                                    'Waist',
                                    '${_selectedSizeSpec!.waistMin}-${_selectedSizeSpec!.waistMax} cm',
                                    profile.waist),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                  const SizedBox(height: 100), // padding at bottom
                ],
              ),
            ),
          ),
        ],
      ),
      bottomSheet: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: AppColors.bgSurface,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.2),
              blurRadius: 10,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: Row(
          children: [
            Expanded(
              child: ElevatedButton(
                onPressed: _selectedSizeSpec != null ? _handleAddToCart : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text('Add to Cart'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSpecMeasurement(String label, String rangeText, double? userValue) {
    final matches = userValue != null;
    return Column(
      children: [
        Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
        const SizedBox(height: 4),
        Text(rangeText, style: const TextStyle(fontWeight: FontWeight.bold)),
        if (matches) ...[
          const SizedBox(height: 4),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: AppColors.success.withOpacity(0.2),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              'Your: ${userValue.toStringAsFixed(0)} cm',
              style: const TextStyle(color: AppColors.success, fontSize: 10, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ],
    );
  }
}
