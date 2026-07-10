import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/api_client.dart';
import '../../core/theme.dart';

class ProductUploadScreen extends ConsumerStatefulWidget {
  const ProductUploadScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<ProductUploadScreen> createState() =>
      _ProductUploadScreenState();
}

class _ProductUploadScreenState extends ConsumerState<ProductUploadScreen> {
  final _skuController = TextEditingController();
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _priceController = TextEditingController();
  final _stockController = TextEditingController();
  final _imageUrlController = TextEditingController();

  String _selectedGender = 'unisex';
  String? _dominantColor = '#E63946';
  bool _isLoading = false;
  String? _errorMessage;

  // Which standard sizes this product is offered in. At least one is required
  // so the product has a size spec (backend Requirement 8.1) and shows up in
  // size search / fit recommendations.
  final Set<String> _selectedSizes = {'M'};

  // Built-in size chart (cm). Ranges are used to build ProductSizeSpec rows so
  // brands don't have to type measurement ranges for a demo upload.
  static const Map<String, Map<String, double>> _sizeChart = {
    'S': {
      'chest_min': 86, 'chest_max': 92, 'waist_min': 71, 'waist_max': 77,
      'hips_min': 89, 'hips_max': 95, 'inseam_min': 76, 'inseam_max': 79,
      'shoulder_width_min': 41, 'shoulder_width_max': 43,
    },
    'M': {
      'chest_min': 92, 'chest_max': 98, 'waist_min': 77, 'waist_max': 83,
      'hips_min': 95, 'hips_max': 101, 'inseam_min': 79, 'inseam_max': 82,
      'shoulder_width_min': 43, 'shoulder_width_max': 45,
    },
    'L': {
      'chest_min': 98, 'chest_max': 104, 'waist_min': 83, 'waist_max': 89,
      'hips_min': 101, 'hips_max': 107, 'inseam_min': 82, 'inseam_max': 85,
      'shoulder_width_min': 45, 'shoulder_width_max': 47,
    },
    'XL': {
      'chest_min': 104, 'chest_max': 112, 'waist_min': 89, 'waist_max': 97,
      'hips_min': 107, 'hips_max': 115, 'inseam_min': 85, 'inseam_max': 88,
      'shoulder_width_min': 47, 'shoulder_width_max': 49,
    },
  };

  final _colorOptions = [
    {'name': 'Red', 'hex': '#E63946'},
    {'name': 'Blue', 'hex': '#457B9D'},
    {'name': 'Black', 'hex': '#1D3557'},
    {'name': 'White', 'hex': '#F1FAEE'},
    {'name': 'Green', 'hex': '#2A9D8F'},
    {'name': 'Yellow', 'hex': '#E9C46A'},
    {'name': 'Pink', 'hex': '#F4A261'},
    {'name': 'Purple', 'hex': '#9D84B7'},
  ];

  @override
  void dispose() {
    _skuController.dispose();
    _nameController.dispose();
    _descriptionController.dispose();
    _priceController.dispose();
    _stockController.dispose();
    _imageUrlController.dispose();
    super.dispose();
  }

  Future<void> _handleUpload() async {
    if (_skuController.text.isEmpty ||
        _nameController.text.isEmpty ||
        _priceController.text.isEmpty) {
      setState(() => _errorMessage = 'Please fill in all required fields');
      return;
    }

    if (_selectedSizes.isEmpty) {
      setState(() => _errorMessage = 'Please select at least one size');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final apiClient = ApiClient();

      final stock = int.tryParse(_stockController.text) ?? 0;
      final sizeSpecs = _selectedSizes.map((label) {
        final chart = _sizeChart[label]!;
        return {
          'size_label': label,
          'stock_quantity': stock,
          ...chart,
        };
      }).toList();

      final data = <String, dynamic>{
        'sku': _skuController.text.trim(),
        'name': _nameController.text.trim(),
        'price': double.parse(_priceController.text),
        'gender_target': _selectedGender,
        'dominant_color_hex': _dominantColor,
        'size_specs': sizeSpecs,
      };
      final description = _descriptionController.text.trim();
      if (description.isNotEmpty) data['description'] = description;
      final imageUrl = _imageUrlController.text.trim();
      if (imageUrl.isNotEmpty) data['image_url'] = imageUrl;

      await apiClient.createProduct(data);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Product uploaded successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        context.go('/brand/products');
      }
    } catch (e) {
      setState(() => _errorMessage = 'Upload failed: $e');
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Upload Product'),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Product Info Section
            Text(
              'Product Information',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),

            TextField(
              controller: _skuController,
              decoration: InputDecoration(
                labelText: 'SKU (Required)',
                hintText: 'e.g., BRAND-TEE-001',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              enabled: !_isLoading,
            ),
            const SizedBox(height: 12),

            TextField(
              controller: _nameController,
              decoration: InputDecoration(
                labelText: 'Product Name (Required)',
                hintText: 'e.g., Classic White T-Shirt',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              enabled: !_isLoading,
            ),
            const SizedBox(height: 12),

            TextField(
              controller: _descriptionController,
              decoration: InputDecoration(
                labelText: 'Description',
                hintText: 'Product details...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              maxLines: 3,
              enabled: !_isLoading,
            ),
            const SizedBox(height: 12),

            TextField(
              controller: _priceController,
              decoration: InputDecoration(
                labelText: 'Price (Required)',
                hintText: 'e.g., 29.99',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              keyboardType: TextInputType.number,
              enabled: !_isLoading,
            ),
            const SizedBox(height: 12),

            TextField(
              controller: _stockController,
              decoration: InputDecoration(
                labelText: 'Stock Quantity (Required)',
                hintText: 'e.g., 100',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              keyboardType: TextInputType.number,
              enabled: !_isLoading,
            ),
            const SizedBox(height: 12),

            TextField(
              controller: _imageUrlController,
              decoration: InputDecoration(
                labelText: 'Image URL (HTTPS)',
                hintText: 'https://...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              enabled: !_isLoading,
            ),
            const SizedBox(height: 24),

            // Gender Target
            Text(
              'Gender Target',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(label: Text('Male'), value: 'male'),
                ButtonSegment(label: Text('Female'), value: 'female'),
                ButtonSegment(label: Text('Unisex'), value: 'unisex'),
              ],
              selected: {_selectedGender},
              onSelectionChanged: (Set<String> newSelection) {
                setState(() {
                  _selectedGender = newSelection.first;
                });
              },
            ),
            const SizedBox(height: 24),

            // Available sizes (at least one required)
            Text(
              'Available Sizes (stock applies to each)',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: _sizeChart.keys.map((label) {
                final selected = _selectedSizes.contains(label);
                return FilterChip(
                  label: Text(label),
                  selected: selected,
                  onSelected: _isLoading
                      ? null
                      : (value) {
                          setState(() {
                            if (value) {
                              _selectedSizes.add(label);
                            } else {
                              _selectedSizes.remove(label);
                            }
                          });
                        },
                );
              }).toList(),
            ),
            const SizedBox(height: 24),

            // Dominant Color
            Text(
              'Dominant Color (for recommendations)',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _colorOptions.map((color) {
                final isSelected = _dominantColor == color['hex'];
                return GestureDetector(
                  onTap: () =>
                      setState(() => _dominantColor = color['hex']),
                  child: Container(
                    width: 80,
                    height: 80,
                    decoration: BoxDecoration(
                      color: Color(
                          int.parse('FF${color['hex']!.replaceFirst('#', '')}',
                              radix: 16)),
                      borderRadius: BorderRadius.circular(8),
                      border: isSelected
                          ? Border.all(color: AppColors.primary, width: 3)
                          : Border.all(color: AppColors.border),
                    ),
                    child: Center(
                      child: Text(
                        color['name']!,
                        style: TextStyle(
                          color: _isLightColor(color['hex']!)
                              ? Colors.black
                              : Colors.white,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),

            if (_errorMessage != null) ...[
              const SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  _errorMessage!,
                  style: TextStyle(color: Colors.red.shade700),
                ),
              ),
            ],

            const SizedBox(height: 24),

            ElevatedButton(
              onPressed: _isLoading ? null : _handleUpload,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: _isLoading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Upload Product'),
            ),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: _isLoading ? null : () => context.go('/brand'),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: const Text('Cancel'),
            ),
          ],
        ),
      ),
    );
  }

  bool _isLightColor(String hexColor) {
    final hex = hexColor.replaceFirst('#', '');
    final r = int.parse(hex.substring(0, 2), radix: 16);
    final g = int.parse(hex.substring(2, 4), radix: 16);
    final b = int.parse(hex.substring(4, 6), radix: 16);
    final brightness = (r * 299 + g * 587 + b * 114) / 1000;
    return brightness > 128;
  }
}
