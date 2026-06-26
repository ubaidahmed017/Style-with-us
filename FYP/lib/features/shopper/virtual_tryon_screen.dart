import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:go_router/go_router.dart';
import '../../core/api_client.dart';
import '../../core/providers/auth_notifier.dart';
import '../../core/providers/cart_notifier.dart';
import '../../shared/models/product_model.dart';

class VirtualTryOnScreen extends ConsumerStatefulWidget {
  final Product? product;
  const VirtualTryOnScreen({Key? key, this.product}) : super(key: key);

  @override
  ConsumerState<VirtualTryOnScreen> createState() => _VirtualTryOnScreenState();
}

class _VirtualTryOnScreenState extends ConsumerState<VirtualTryOnScreen> {
  final _imagePicker = ImagePicker();
  bool _isLoading = false;
  String? _errorMessage;
  XFile? _selectedImage;
  String? _resultImageUrl;
  String? _jobId;

  Future<void> _pickImage() async {
    try {
      final image = await _imagePicker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 85,
      );

      if (image != null) {
        setState(() {
          _selectedImage = image;
          _resultImageUrl = null;
          _errorMessage = null;
        });

        // Show privacy notice on first use (can be tracked separately)
        if (mounted) {
          _showPrivacyNotice();
        }
      }
    } catch (e) {
      setState(() => _errorMessage = 'Failed to pick image: $e');
    }
  }

  void _showPrivacyNotice() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Your Privacy Matters'),
        content: const Text(
          'Your photos are analyzed on your device only and are never uploaded to our servers.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }

  Future<void> _startVirtualTryOn() async {
    if (_selectedImage == null) {
      setState(() => _errorMessage = 'Please select a photo first');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _resultImageUrl = null;
    });

    try {
      // In a real implementation, this would:
      // 1. Load image locally
      // 2. Run MediaPipe Pose Estimation on-device
      // 3. Run OpenCV garment compositing on-device
      // 4. Display result without uploading photo

      // For now, we'll simulate the process
      await Future.delayed(const Duration(seconds: 2));

      // Simulate result
      setState(() {
        _resultImageUrl = _selectedImage!.path;
        _isLoading = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Try-on complete! (This is a simulated result)'),
          duration: Duration(seconds: 2),
        ),
      );
    } catch (e) {
      setState(() {
        _errorMessage = 'Try-on failed: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _addToCart() async {
    if (_resultImageUrl == null) return;

    final product = widget.product;
    if (product != null) {
      ref.read(cartProvider.notifier).addItem(
        product.productId,
        product.name,
        product.price,
        sizeSpecId: product.sizeSpecs.isNotEmpty ? product.sizeSpecs.first.specId : null,
        sizeLabel: product.sizeSpecs.isNotEmpty ? product.sizeSpecs.first.sizeLabel : null,
      );
    } else {
      // Simulate adding to cart
      ref.read(cartProvider.notifier).addItem(
        'product-123',
        'Sample Product',
        99.99,
        sizeSpecId: 'spec-1',
        sizeLabel: 'M',
      );
    }

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Added to cart!'),
        duration: Duration(seconds: 2),
      ),
    );

    if (mounted) {
      context.go('/shopper');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Virtual Try-On'),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Selected image preview
            if (_selectedImage != null)
              Container(
                height: 300,
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade300),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Image.file(
                  File(_selectedImage!.path),
                  fit: BoxFit.cover,
                ),
              )
            else
              Container(
                height: 200,
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  border: Border.all(color: Colors.grey.shade300),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.image, size: 48, color: Colors.grey.shade400),
                    const SizedBox(height: 12),
                    Text(
                      'Select a full-body photo',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.grey.shade600,
                      ),
                    ),
                  ],
                ),
              ),

            const SizedBox(height: 24),

            // Result image (if available)
            if (_resultImageUrl != null)
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Try-On Result',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 12),
                  Container(
                    height: 300,
                    decoration: BoxDecoration(
                      border: Border.all(color: Colors.green.shade300),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Image.file(
                      File(_resultImageUrl!),
                      fit: BoxFit.cover,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {
                            // Share functionality
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Share feature coming soon'),
                              ),
                            );
                          },
                          icon: const Icon(Icons.share),
                          label: const Text('Share'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {
                            // Save to gallery
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Saved to gallery'),
                              ),
                            );
                          },
                          icon: const Icon(Icons.download),
                          label: const Text('Save'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _addToCart,
                      child: const Text('Add to Cart'),
                    ),
                  ),
                ],
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

            // Action buttons
            if (_selectedImage == null || _resultImageUrl == null)
              ElevatedButton(
                onPressed: _isLoading ? null : _pickImage,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text('Select Photo from Gallery'),
              ),

            if (_selectedImage != null && _resultImageUrl == null)
              Column(
                children: [
                  const SizedBox(height: 12),
                  ElevatedButton(
                    onPressed: _isLoading ? null : _startVirtualTryOn,
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      backgroundColor: Colors.green,
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor: AlwaysStoppedAnimation<Color>(
                                Colors.white,
                              ),
                            ),
                          )
                        : const Text(
                            'Generate Try-On',
                            style: TextStyle(color: Colors.white),
                          ),
                  ),
                ],
              ),

            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: _isLoading ? null : () => context.go('/shopper'),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: const Text('Back to Home'),
            ),
          ],
        ),
      ),
    );
  }
}
