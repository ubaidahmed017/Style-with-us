import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../../shared/models/product_model.dart';

class WishlistNotifier extends Notifier<List<Product>> {
  static const String _wishlistKey = 'user_wishlist';

  @override
  List<Product> build() {
    _loadWishlistFromStorage();
    return [];
  }

  Future<void> _loadWishlistFromStorage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final wishlistJson = prefs.getString(_wishlistKey);
      if (wishlistJson != null) {
        final List<dynamic> decoded = jsonDecode(wishlistJson);
        final products = decoded
            .map((item) => Product.fromJson(item as Map<String, dynamic>))
            .toList();
        state = products;
      }
    } catch (e) {
      // Handle error silently
    }
  }

  Future<void> _saveWishlistToStorage(List<Product> products) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final wishlistJson = jsonEncode(products.map((item) => {
        'product_id': item.productId,
        'brand_id': item.brandId,
        'sku': item.sku,
        'name': item.name,
        'description': item.description,
        'price': item.price,
        'image_url': item.imageUrl,
        'garment_image_url': item.garmentImageUrl,
        'gender_target': item.genderTarget,
        'dominant_color_hex': item.dominantColorHex,
        'size_specs': item.sizeSpecs.map((spec) => {
          'spec_id': spec.specId,
          'size_label': spec.sizeLabel,
          'stock_quantity': spec.stockQuantity,
          'chest_min': spec.chestMin,
          'chest_max': spec.chestMax,
          'waist_min': spec.waistMin,
          'waist_max': spec.waistMax,
          'hips_min': spec.hipsMin,
          'hips_max': spec.hipsMax,
          'inseam_min': spec.inseamMin,
          'inseam_max': spec.inseamMax,
          'shoulder_min': spec.shoulderMin,
          'shoulder_max': spec.shoulderMax,
        }).toList(),
        'why_recommended': item.whyRecommended,
      }).toList());
      await prefs.setString(_wishlistKey, wishlistJson);
    } catch (e) {
      // Handle error silently
    }
  }

  void toggleProduct(Product product) {
    final isExist = state.any((item) => item.productId == product.productId);
    List<Product> updatedList;
    if (isExist) {
      updatedList = state.where((item) => item.productId != product.productId).toList();
    } else {
      updatedList = [...state, product];
    }
    state = updatedList;
    _saveWishlistToStorage(updatedList);
  }

  bool isFavorite(String productId) {
    return state.any((item) => item.productId == productId);
  }
}

final wishlistProvider = NotifierProvider<WishlistNotifier, List<Product>>(() {
  return WishlistNotifier();
});
