import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/api_client.dart';

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

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final apiClient = ApiClient();

      await apiClient.dio.post('/inventory/products', data: {
        'sku': _skuController.text.trim(),
        'name': _nameController.text.trim(),
        'description': _descriptionController.text.trim(),
        'price': double.parse(_priceController.text),
        'stock_quantity': int.parse(_stockController.text),
        'image_url': _imageUrlController.text.trim(),
        'gender_target': _selectedGender,
        'dominant_color_hex': _dominantColor,
      });

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
                          ? Border.all(color: Colors.blue, width: 3)
                          : Border.all(color: Colors.grey.shade300),
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
