class ProductSizeSpec {
  final String specId;
  final String sizeLabel;
  final int stockQuantity;
  final double? chestMin;
  final double? chestMax;
  final double? waistMin;
  final double? waistMax;
  final double? hipsMin;
  final double? hipsMax;
  final double? inseamMin;
  final double? inseamMax;
  final double? shoulderMin;
  final double? shoulderMax;

  ProductSizeSpec({
    required this.specId,
    required this.sizeLabel,
    required this.stockQuantity,
    this.chestMin,
    this.chestMax,
    this.waistMin,
    this.waistMax,
    this.hipsMin,
    this.hipsMax,
    this.inseamMin,
    this.inseamMax,
    this.shoulderMin,
    this.shoulderMax,
  });

  factory ProductSizeSpec.fromJson(Map<String, dynamic> json) {
    return ProductSizeSpec(
      specId: json['spec_id'],
      sizeLabel: json['size_label'],
      stockQuantity: json['stock_quantity'],
      chestMin: json['chest_min']?.toDouble(),
      chestMax: json['chest_max']?.toDouble(),
      waistMin: json['waist_min']?.toDouble(),
      waistMax: json['waist_max']?.toDouble(),
      hipsMin: json['hips_min']?.toDouble(),
      hipsMax: json['hips_max']?.toDouble(),
      inseamMin: json['inseam_min']?.toDouble(),
      inseamMax: json['inseam_max']?.toDouble(),
      // Backend serializes these as shoulder_width_min/max.
      shoulderMin: json['shoulder_width_min']?.toDouble(),
      shoulderMax: json['shoulder_width_max']?.toDouble(),
    );
  }

  bool fitsMeasurement({
    double? chest,
    double? waist,
    double? hips,
    double? inseam,
  }) {
    if (chest != null && (chestMin == null || chestMax == null)) return false;
    if (chest != null && (chest < chestMin! || chest > chestMax!)) return false;

    if (waist != null && (waistMin == null || waistMax == null)) return false;
    if (waist != null && (waist < waistMin! || waist > waistMax!)) return false;

    if (hips != null && (hipsMin == null || hipsMax == null)) return false;
    if (hips != null && (hips < hipsMin! || hips > hipsMax!)) return false;

    if (inseam != null && (inseamMin == null || inseamMax == null)) return false;
    if (inseam != null && (inseam < inseamMin! || inseam > inseamMax!)) return false;

    return true;
  }
}

class Product {
  final String productId;
  final String brandId;
  final String sku;
  final String name;
  final String? description;
  final double price;
  final String imageUrl;
  final String? garmentImageUrl;
  final String genderTarget; // male, female, unisex
  final String? dominantColorHex;
  final List<ProductSizeSpec> sizeSpecs;
  final String? whyRecommended;

  Product({
    required this.productId,
    required this.brandId,
    required this.sku,
    required this.name,
    this.description,
    required this.price,
    required this.imageUrl,
    this.garmentImageUrl,
    required this.genderTarget,
    this.dominantColorHex,
    required this.sizeSpecs,
    this.whyRecommended,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      productId: json['product_id'],
      brandId: json['brand_id'],
      sku: json['sku'],
      name: json['name'],
      description: json['description'],
      price: (json['price'] as num).toDouble(),
      // image_url can be null for products uploaded without an image.
      imageUrl: json['image_url'] ?? '',
      garmentImageUrl: json['garment_image_url'],
      genderTarget: json['gender_target'],
      dominantColorHex: json['dominant_color_hex'],
      sizeSpecs: (json['size_specs'] as List? ?? [])
          .map((spec) => ProductSizeSpec.fromJson(spec))
          .toList(),
      whyRecommended: json['why_recommended'],
    );
  }

  bool isGenderAppropriate(String userGender) {
    if (genderTarget == 'unisex') return true;
    if (userGender == 'non_binary') return true;
    return genderTarget == userGender;
  }

  ProductSizeSpec? findMatchingSize({
    double? chest,
    double? waist,
    double? hips,
    double? inseam,
  }) {
    try {
      return sizeSpecs.firstWhere((spec) =>
          spec.fitsMeasurement(
            chest: chest,
            waist: waist,
            hips: hips,
            inseam: inseam,
          ));
    } catch (e) {
      return null;
    }
  }

  bool hasSizeLabel(String label) {
    return sizeSpecs.any((spec) => spec.sizeLabel == label);
  }

  bool hasStock() {
    return sizeSpecs.any((spec) => spec.stockQuantity > 0);
  }
}

class Brand {
  final String brandId;
  final String companyName;
  final String? logoUrl;

  Brand({
    required this.brandId,
    required this.companyName,
    this.logoUrl,
  });

  factory Brand.fromJson(Map<String, dynamic> json) {
    return Brand(
      brandId: json['brand_id'],
      companyName: json['company_name'],
      logoUrl: json['logo_url'],
    );
  }
}

class RecommendedOutfitsGroup {
  final Brand? brand;
  final List<Product> products;
  final String section; // "exact_match", "similar_styles", "by_brand"

  RecommendedOutfitsGroup({
    this.brand,
    required this.products,
    required this.section,
  });
}
