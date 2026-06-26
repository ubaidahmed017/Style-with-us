import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../shared/models/product_model.dart';
import '../api_client.dart';

class RecommendationsNotifier extends AsyncNotifier<List<RecommendedOutfitsGroup>> {
  late final ApiClient _apiClient;

  @override
  Future<List<RecommendedOutfitsGroup>> build() async {
    _apiClient = ApiClient();
    return _fetchRecommendations();
  }

  Future<List<RecommendedOutfitsGroup>> _fetchRecommendations() async {
    try {
      final response = await _apiClient.getRecommendations();

      if (response.statusCode == 200) {
        final data = response.data;

        // Parse the response structure
        // Expected format: {
        //   "exact_match": [...],
        //   "similar_styles": [...],
        //   "by_brand": [{"brand": {...}, "products": [...]}]
        // }

        final groups = <RecommendedOutfitsGroup>[];

        // Add exact matches
        if (data['exact_match'] != null) {
          final products = (data['exact_match'] as List)
              .map((p) => Product.fromJson(p))
              .toList();
          groups.add(RecommendedOutfitsGroup(
            products: products,
            section: 'exact_match',
          ));
        }

        // Add similar styles
        if (data['similar_styles'] != null) {
          final products = (data['similar_styles'] as List)
              .map((p) => Product.fromJson(p))
              .toList();
          groups.add(RecommendedOutfitsGroup(
            products: products,
            section: 'similar_styles',
          ));
        }

        // Add by brand
        if (data['by_brand'] != null) {
          final brandGroups = (data['by_brand'] as List).map((groupData) {
            final brand = Brand.fromJson(groupData['brand']);
            final products = (groupData['products'] as List)
                .map((p) => Product.fromJson(p))
                .toList();
            return RecommendedOutfitsGroup(
              brand: brand,
              products: products,
              section: 'by_brand',
            );
          }).toList();
          groups.addAll(brandGroups);
        }

        return groups;
      }
      return [];
    } catch (e) {
      rethrow;
    }
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => _fetchRecommendations());
  }
}

final recommendationsProvider = AsyncNotifierProvider<
    RecommendationsNotifier,
    List<RecommendedOutfitsGroup>>(() {
  return RecommendationsNotifier();
});

final hasRecommendationsProvider = Provider<bool>((ref) {
  return ref.watch(recommendationsProvider).when(
    data: (groups) => groups.isNotEmpty,
    loading: () => false,
    error: (_, __) => false,
  );
});
