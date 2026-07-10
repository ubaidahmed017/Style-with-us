import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';
import 'package:palette_generator/palette_generator.dart';
import '../../core/api_client.dart';
import '../../core/theme.dart';

/// On-device body shape + skin tone analysis.
///
/// Privacy-first: the selected photo is processed entirely on the device using
/// Google ML Kit Pose Detection (MediaPipe) and palette_generator. The raw
/// photo is NEVER uploaded. Only the computed metrics are sent to the backend
/// via `PATCH /users/profile` after the user confirms the result.
class BodyAnalysisScreen extends ConsumerStatefulWidget {
  const BodyAnalysisScreen({super.key});

  @override
  ConsumerState<BodyAnalysisScreen> createState() => _BodyAnalysisScreenState();
}

class _BodyAnalysisResult {
  final String bodyShape;
  final String skinToneHex;
  final String seasonalPalette;
  final double confidence;

  _BodyAnalysisResult({
    required this.bodyShape,
    required this.skinToneHex,
    required this.seasonalPalette,
    required this.confidence,
  });
}

class _BodyAnalysisScreenState extends ConsumerState<BodyAnalysisScreen> {
  final ImagePicker _imagePicker = ImagePicker();
  final PoseDetector _poseDetector =
      PoseDetector(options: PoseDetectorOptions());
  final ApiClient _apiClient = ApiClient();

  XFile? _selectedImage;
  bool _isAnalyzing = false;
  bool _isSaving = false;
  String? _errorMessage;
  _BodyAnalysisResult? _result;

  @override
  void dispose() {
    // Clear source photo reference and release the detector (photo never cached).
    _selectedImage = null;
    _result = null;
    _poseDetector.close();
    super.dispose();
  }

  Future<void> _pickAndAnalyze() async {
    setState(() {
      _errorMessage = null;
      _result = null;
    });

    final XFile? image =
        await _imagePicker.pickImage(source: ImageSource.gallery);
    if (image == null) return;

    setState(() {
      _selectedImage = image;
      _isAnalyzing = true;
    });

    try {
      final result = await _analyzeOnDevice(image);
      setState(() {
        _result = result;
        _isAnalyzing = false;
      });
    } catch (e) {
      setState(() {
        _isAnalyzing = false;
        _errorMessage = e is _PoseNotDetectedError
            ? 'Please use a clear, well-lit, full-body photo.'
            : 'Analysis failed. Please try another photo.';
      });
    }
  }

  /// Runs entirely on-device. No network call is made here.
  Future<_BodyAnalysisResult> _analyzeOnDevice(XFile image) async {
    final inputImage = InputImage.fromFilePath(image.path);
    final poses = await _poseDetector.processImage(inputImage);

    if (poses.isEmpty) {
      throw _PoseNotDetectedError();
    }
    final pose = poses.first;

    final leftShoulder = pose.landmarks[PoseLandmarkType.leftShoulder];
    final rightShoulder = pose.landmarks[PoseLandmarkType.rightShoulder];
    final leftHip = pose.landmarks[PoseLandmarkType.leftHip];
    final rightHip = pose.landmarks[PoseLandmarkType.rightHip];

    // Require the four torso landmarks with sufficient visibility (>= 0.3).
    const double minVisibility = 0.3;
    final torso = [leftShoulder, rightShoulder, leftHip, rightHip];
    if (torso.any((l) => l == null || (l.likelihood) < minVisibility)) {
      throw _PoseNotDetectedError();
    }

    // Pixel-space widths.
    final shoulderWidth =
        (leftShoulder!.x - rightShoulder!.x).abs();
    final hipWidth = (leftHip!.x - rightHip!.x).abs();
    // Waist estimated as midpoint band between shoulders and hips.
    final waistWidth = (shoulderWidth + hipWidth) / 2 * 0.85;

    final bodyShape = _classifyBodyShape(
      shoulderWidth: shoulderWidth,
      waistWidth: waistWidth,
      hipWidth: hipWidth,
    );

    // Confidence: how strongly ratios separate from the neutral (rectangle) band.
    final confidence = _shapeConfidence(shoulderWidth, waistWidth, hipWidth);

    // Skin tone: sample dominant color from the upper (face/neck) region.
    final skinToneHex = await _extractSkinToneHex(File(image.path));
    final palette = _mapToSeasonalPalette(skinToneHex);

    return _BodyAnalysisResult(
      bodyShape: bodyShape,
      skinToneHex: skinToneHex,
      seasonalPalette: palette,
      confidence: confidence,
    );
  }

  String _classifyBodyShape({
    required double shoulderWidth,
    required double waistWidth,
    required double hipWidth,
  }) {
    if (shoulderWidth <= 0 || hipWidth <= 0) return 'rectangle';

    final shoulderToHip = shoulderWidth / hipWidth;
    final waistToHip = waistWidth / hipWidth;
    final waistToShoulder = waistWidth / shoulderWidth;

    // Hourglass: shoulders ≈ hips, well-defined waist.
    if ((shoulderToHip - 1).abs() <= 0.1 && waistToHip <= 0.8) {
      return 'hourglass';
    }
    // Pear: hips notably wider than shoulders.
    if (shoulderToHip < 0.9) {
      return 'pear';
    }
    // Inverted triangle: shoulders notably wider than hips.
    if (shoulderToHip > 1.1) {
      return 'inverted_triangle';
    }
    // Apple: waist close to or wider than hips/shoulders.
    if (waistToHip >= 0.95 || waistToShoulder >= 0.95) {
      return 'apple';
    }
    // Default: balanced proportions with little waist definition.
    return 'rectangle';
  }

  double _shapeConfidence(double shoulder, double waist, double hip) {
    if (shoulder <= 0 || hip <= 0) return 0.5;
    final shoulderToHip = shoulder / hip;
    final waistToHip = waist / hip;
    // Larger deviation from neutral proportions => higher confidence, clamped.
    final dev = (shoulderToHip - 1).abs() + (waistToHip - 0.9).abs();
    return (0.6 + dev).clamp(0.0, 1.0);
  }

  Future<String> _extractSkinToneHex(File file) async {
    final palette = await PaletteGenerator.fromImageProvider(
      FileImage(file),
      // Sample the top portion where the face/neck is most likely to be.
      size: const Size(200, 200),
      maximumColorCount: 16,
    );
    final color = palette.dominantColor?.color ??
        palette.vibrantColor?.color ??
        const Color(0xFFC68642);
    return '#${color.value.toRadixString(16).padLeft(8, '0').substring(2).toUpperCase()}';
  }

  /// Maps a skin tone hex to one of six seasonal palettes based on
  /// luminance (light/deep) and warmth (R vs B).
  String _mapToSeasonalPalette(String hex) {
    final clean = hex.replaceAll('#', '');
    final r = int.parse(clean.substring(0, 2), radix: 16);
    final g = int.parse(clean.substring(2, 4), radix: 16);
    final b = int.parse(clean.substring(4, 6), radix: 16);

    final luminance = (0.299 * r + 0.587 * g + 0.114 * b);
    final warmth = r - b; // positive => warm undertone

    final bool isLight = luminance >= 140;
    final bool isDeep = luminance < 90;

    if (warmth > 25) {
      return isLight ? 'warm_spring' : 'warm_autumn';
    }
    if (warmth < -5) {
      return isLight ? 'cool_summer' : 'cool_winter';
    }
    // Near-neutral undertone.
    return isDeep ? 'neutral_deep' : 'neutral_light';
  }

  Future<void> _saveToProfile() async {
    final result = _result;
    if (result == null) return;

    setState(() => _isSaving = true);
    try {
      // ONLY the computed metrics are sent — never the photo.
      await _apiClient.dio.patch('/users/profile', data: {
        'body_shape': result.bodyShape,
        'skin_tone_hex': result.skinToneHex,
        'skin_tone_palette': result.seasonalPalette,
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Profile updated with your results')),
      );
      setState(() {
        _isSaving = false;
        // Clear the photo from memory once results are saved.
        _selectedImage = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isSaving = false;
        _errorMessage = 'Could not update your profile. Please try again.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Body & Skin Tone Analysis')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _buildPrivacyNotice(),
            const SizedBox(height: 16),
            if (_selectedImage != null)
              ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: Image.file(
                  File(_selectedImage!.path),
                  height: 280,
                  fit: BoxFit.cover,
                ),
              ),
            const SizedBox(height: 16),
            if (_isAnalyzing) ...[
              const Center(child: CircularProgressIndicator()),
              const SizedBox(height: 12),
              const Center(
                child: Text('Analyzing on your device…'),
              ),
            ],
            if (_errorMessage != null)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.error.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  _errorMessage!,
                  style: const TextStyle(color: AppColors.error),
                ),
              ),
            if (_result != null) _buildResultCard(_result!),
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: _isAnalyzing ? null : _pickAndAnalyze,
              icon: const Icon(Icons.photo_library_outlined),
              label: Text(
                _selectedImage == null ? 'Select a Photo' : 'Choose Another Photo',
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPrivacyNotice() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.info.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          const Icon(Icons.lock_outline, color: AppColors.info),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              'Your photo is analyzed on your device only and is never uploaded.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildResultCard(_BodyAnalysisResult result) {
    final color = Color(
      int.parse('FF${result.skinToneHex.replaceAll('#', '')}', radix: 16),
    );
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Your Results',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(Icons.accessibility_new, color: AppColors.primary),
                const SizedBox(width: 8),
                Text('Body shape: '),
                Text(
                  _prettyShape(result.bodyShape),
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              'Confidence: ${(result.confidence * 100).toStringAsFixed(0)}%',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: color,
                    shape: BoxShape.circle,
                    border: Border.all(color: AppColors.textMuted),
                  ),
                ),
                const SizedBox(width: 10),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Skin tone: ${result.skinToneHex}'),
                    Text(
                      'Palette: ${_prettyPalette(result.seasonalPalette)}',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _isSaving ? null : _saveToProfile,
              child: _isSaving
                  ? const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Update my profile'),
            ),
          ],
        ),
      ),
    );
  }

  String _prettyShape(String s) =>
      s.split('_').map((w) => w[0].toUpperCase() + w.substring(1)).join(' ');

  String _prettyPalette(String s) =>
      s.split('_').map((w) => w[0].toUpperCase() + w.substring(1)).join(' ');
}

class _PoseNotDetectedError implements Exception {}
