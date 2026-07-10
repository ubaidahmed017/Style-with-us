import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../shared/models/product_model.dart';
import '../api_client.dart';

class ProductsFilter {
  final String? gender;
  final String? search;
  final double? maxPrice;
  final String? brandId;

  ProductsFilter({
    this.gender,
    this.search,
    this.maxPrice,
    this.brandId,
  });

  ProductsFilter copyWith({
    String? gender,
    String? search,
    double? maxPrice,
    String? brandId,
    bool clearGender = false,
    bool clearSearch = false,
    bool clearMaxPrice = false,
    bool clearBrandId = false,
  }) {
    return ProductsFilter(
      gender: clearGender ? null : (gender ?? this.gender),
      search: clearSearch ? null : (search ?? this.search),
      maxPrice: clearMaxPrice ? null : (maxPrice ?? this.maxPrice),
      brandId: clearBrandId ? null : (brandId ?? this.brandId),
    );
  }
}

class ProductsNotifier extends AsyncNotifier<List<Product>> {
  late final ApiClient _apiClient;
  ProductsFilter _filter = ProductsFilter();

  @override
  Future<List<Product>> build() async {
    _apiClient = ApiClient();
    return _fetchProducts();
  }

  ProductsFilter get filter => _filter;

  Future<List<Product>> _fetchProducts() async {
    try {
      // Fetch from API
      // Since it's a localhost:8000 URL which might fail if backend is not started,
      // we wrap it in a try-catch and fallback to high-quality mock products.
      final response = await _apiClient.getProducts(
        gender: _filter.gender,
        brandId: _filter.brandId,
      );

      if (response.statusCode == 200) {
        // The backend returns a plain JSON array of products. (Older shapes
        // wrapped it in {"products": [...]}, so handle both.)
        final raw = response.data;
        final List<dynamic> data =
            raw is List ? raw : (raw['products'] as List? ?? []);
        var products = data
            .map((p) => Product.fromJson(p as Map<String, dynamic>))
            .toList();
        return _applyClientFilters(products);
      }
    } catch (e) {
      // Fallback to mock products on connection error
    }

    return _getMockProducts();
  }

  List<Product> _applyClientFilters(List<Product> products) {
    var filtered = [...products];

    if (_filter.gender != null) {
      filtered = filtered
          .where((p) => p.genderTarget == _filter.gender || p.genderTarget == 'unisex')
          .toList();
    }

    if (_filter.search != null && _filter.search!.isNotEmpty) {
      final query = _filter.search!.toLowerCase();
      filtered = filtered
          .where((p) =>
              p.name.toLowerCase().contains(query) ||
              (p.description?.toLowerCase().contains(query) ?? false))
          .toList();
    }

    if (_filter.maxPrice != null) {
      filtered = filtered.where((p) => p.price <= _filter.maxPrice!).toList();
    }

    if (_filter.brandId != null) {
      filtered = filtered.where((p) => p.brandId == _filter.brandId).toList();
    }

    return filtered;
  }

  Future<void> setGenderFilter(String? gender) async {
    state = const AsyncValue.loading();
    _filter = _filter.copyWith(
      gender: gender,
      clearGender: gender == null,
    );
    state = await AsyncValue.guard(() => _fetchProducts());
  }

  Future<void> setSearchFilter(String? search) async {
    state = const AsyncValue.loading();
    _filter = _filter.copyWith(
      search: search,
      clearSearch: search == null || search.isEmpty,
    );
    state = await AsyncValue.guard(() => _fetchProducts());
  }

  Future<void> setMaxPriceFilter(double? maxPrice) async {
    state = const AsyncValue.loading();
    _filter = _filter.copyWith(
      maxPrice: maxPrice,
      clearMaxPrice: maxPrice == null,
    );
    state = await AsyncValue.guard(() => _fetchProducts());
  }

  Future<void> setBrandFilter(String? brandId) async {
    state = const AsyncValue.loading();
    _filter = _filter.copyWith(
      brandId: brandId,
      clearBrandId: brandId == null,
    );
    state = await AsyncValue.guard(() => _fetchProducts());
  }

  Future<void> clearAllFilters() async {
    state = const AsyncValue.loading();
    _filter = ProductsFilter();
    state = await AsyncValue.guard(() => _fetchProducts());
  }

  List<Product> _getMockProducts() {
    final allMocks = [
      Product(
        productId: 'prod-1',
        brandId: 'brand-1',
        sku: 'BRAND-TEE-001',
        name: 'Classic White T-Shirt',
        description: 'A premium cotton t-shirt with a modern fit. Extremely breathable and durable, perfect for everyday casual wear.',
        price: 29.99,
        imageUrl: 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=600&auto=format&fit=crop&q=80',
        genderTarget: 'unisex',
        dominantColorHex: '#F1FAEE',
        sizeSpecs: [
          ProductSizeSpec(specId: 's1', sizeLabel: 'S', stockQuantity: 25, chestMin: 85, chestMax: 93, waistMin: 70, waistMax: 78),
          ProductSizeSpec(specId: 's2', sizeLabel: 'M', stockQuantity: 40, chestMin: 93, chestMax: 101, waistMin: 78, waistMax: 86),
          ProductSizeSpec(specId: 's3', sizeLabel: 'L', stockQuantity: 15, chestMin: 101, chestMax: 109, waistMin: 86, waistMax: 94),
        ],
      ),
      Product(
        productId: 'prod-2',
        brandId: 'brand-1',
        sku: 'BRAND-JEANS-001',
        name: 'Slim Fit Black Jeans',
        description: 'Stretch denim jeans in black. Five-pocket styling, zip-fly, and tailored fit for an effortlessly clean silhouette.',
        price: 79.99,
        imageUrl: 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=600&auto=format&fit=crop&q=80',
        genderTarget: 'male',
        dominantColorHex: '#1D3557',
        sizeSpecs: [
          ProductSizeSpec(specId: 'j1', sizeLabel: 'M', stockQuantity: 10, waistMin: 78, waistMax: 86, inseamMin: 76, inseamMax: 82),
          ProductSizeSpec(specId: 'j2', sizeLabel: 'L', stockQuantity: 12, waistMin: 86, waistMax: 94, inseamMin: 80, inseamMax: 86),
        ],
      ),
      Product(
        productId: 'prod-3',
        brandId: 'brand-2',
        sku: 'BRAND-DRESS-001',
        name: 'Floral Summer Dress',
        description: 'Lightweight linen blend dress with all-over floral print. Features a sweetheart neckline, puff sleeves, and a flowing skirt.',
        price: 95.00,
        imageUrl: 'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=600&auto=format&fit=crop&q=80',
        genderTarget: 'female',
        dominantColorHex: '#F4A261',
        sizeSpecs: [
          ProductSizeSpec(specId: 'd1', sizeLabel: 'S', stockQuantity: 8, chestMin: 80, chestMax: 88, waistMin: 62, waistMax: 70, hipsMin: 86, hipsMax: 94),
          ProductSizeSpec(specId: 'd2', sizeLabel: 'M', stockQuantity: 14, chestMin: 88, chestMax: 96, waistMin: 70, waistMax: 78, hipsMin: 94, hipsMax: 102),
        ],
      ),
      Product(
        productId: 'prod-4',
        brandId: 'brand-2',
        sku: 'BRAND-JCK-002',
        name: 'Suede Biker Jacket',
        description: 'Premium suede leather biker jacket with metallic zip accents. Fully lined interior, zip cuffs, and an asymmetric front zip closure.',
        price: 189.99,
        imageUrl: 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600&auto=format&fit=crop&q=80',
        genderTarget: 'unisex',
        dominantColorHex: '#9D84B7',
        sizeSpecs: [
          ProductSizeSpec(specId: 'jk1', sizeLabel: 'S', stockQuantity: 5, chestMin: 86, chestMax: 94),
          ProductSizeSpec(specId: 'jk2', sizeLabel: 'M', stockQuantity: 9, chestMin: 94, chestMax: 102),
          ProductSizeSpec(specId: 'jk3', sizeLabel: 'L', stockQuantity: 4, chestMin: 102, chestMax: 110),
        ],
      ),
      Product(
        productId: 'prod-5',
        brandId: 'brand-3',
        sku: 'BRAND-HD-003',
        name: 'Oversized Pastel Hoodie',
        description: 'Ultra-soft fleece hoodie in a pastel lilac shade. Features drop shoulders, a spacious kangaroo pocket, and ribbed trims.',
        price: 65.00,
        imageUrl: 'https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=600&auto=format&fit=crop&q=80',
        genderTarget: 'unisex',
        dominantColorHex: '#9D84B7',
        sizeSpecs: [
          ProductSizeSpec(specId: 'h1', sizeLabel: 'S', stockQuantity: 15, chestMin: 85, chestMax: 95),
          ProductSizeSpec(specId: 'h2', sizeLabel: 'M', stockQuantity: 22, chestMin: 95, chestMax: 105),
          ProductSizeSpec(specId: 'h3', sizeLabel: 'L', stockQuantity: 18, chestMin: 105, chestMax: 115),
        ],
      ),
      Product(
        productId: 'prod-6',
        brandId: 'brand-3',
        sku: 'BRAND-SK-004',
        name: 'Pleated Midi Skirt',
        description: 'Elegant pleated midi skirt in emerald green. Designed with a high-rise elasticated waistband and flowing, clean pleats.',
        price: 49.99,
        imageUrl: 'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=600&auto=format&fit=crop&q=80',
        genderTarget: 'female',
        dominantColorHex: '#2A9D8F',
        sizeSpecs: [
          ProductSizeSpec(specId: 'sk1', sizeLabel: 'S', stockQuantity: 12, waistMin: 60, waistMax: 68, hipsMin: 88, hipsMax: 96),
          ProductSizeSpec(specId: 'sk2', sizeLabel: 'M', stockQuantity: 15, waistMin: 68, waistMax: 76, hipsMin: 96, hipsMax: 104),
        ],
      ),
    ];

    return _applyClientFilters(allMocks);
  }
}

final productsProvider = AsyncNotifierProvider<ProductsNotifier, List<Product>>(() {
  return ProductsNotifier();
});
