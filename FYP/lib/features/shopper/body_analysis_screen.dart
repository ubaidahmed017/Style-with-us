import 'dart:io';
import 'dart:math' as math;
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';
import '../../core/api_client.dart';
import '../../core/theme.dart';

/// On-device body shape + skin tone analysis.
///
/// Privacy-first: the selected photo is processed entirely on the device —
/// Google ML Kit Pose Detection (MediaPipe) locates the face/torso, then skin
/// pixels are sampled directly (YCbCr mask + median). The raw photo is NEVER
/// uploaded. Only the computed metrics are sent to the backend via
/// `PATCH /users/profile` after the user confirms (or manually adjusts) the
/// result. The server recomputes the seasonal palette from the hex, so the
/// backend classifier (services/color.py) stays the single source of truth.
class BodyAnalysisScreen extends ConsumerStatefulWidget {
  const BodyAnalysisScreen({super.key});

  @override
  ConsumerState<BodyAnalysisScreen> createState() => _BodyAnalysisScreenState();
}

class _BodyAnalysisResult {
  final String bodyShape;
  // Nullable: when skin sampling fails (occluded face, extreme lighting) the
  // user picks their tone manually instead of getting a wrong guess.
  final String? skinToneHex;
  final String? seasonalPalette;
  final double confidence;

  _BodyAnalysisResult({
    required this.bodyShape,
    required this.skinToneHex,
    required this.seasonalPalette,
    required this.confidence,
  });

  _BodyAnalysisResult withSkinTone(String hex, String palette) =>
      _BodyAnalysisResult(
        bodyShape: bodyShape,
        skinToneHex: hex,
        seasonalPalette: palette,
        confidence: confidence,
      );
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

    // Skin tone: sample actual skin pixels from the face/cheek region.
    // Null when sampling isn't trustworthy — the UI then offers a manual
    // swatch picker instead of guessing from the background.
    final skinToneHex = await _sampleSkinTone(File(image.path), pose);
    final palette =
        skinToneHex != null ? _paletteFromHex(skinToneHex) : null;

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

  String _hex(Color c) =>
      '#${c.value.toRadixString(16).padLeft(8, '0').substring(2).toUpperCase()}';

  // Landmark confidence floor for the face points used in skin sampling.
  // MediaPipe returns positions for ALL landmarks even when the person faces
  // away — without this check a back-facing photo samples hair/background.
  static const double _faceMinLikelihood = 0.3;

  /// Median skin pixels in a box around the face (nose/eye landmarks).
  ///
  /// Returns null (→ manual picker) rather than guessing when: the face
  /// landmarks aren't confidently visible, the image can't be decoded, or too
  /// few pixels pass the skin mask.
  Future<String?> _sampleSkinTone(File file, Pose pose) async {
    try {
      final nose = pose.landmarks[PoseLandmarkType.nose];
      final leftEye = pose.landmarks[PoseLandmarkType.leftEye];
      final rightEye = pose.landmarks[PoseLandmarkType.rightEye];
      if (nose == null || leftEye == null || rightEye == null) return null;
      if (nose.likelihood < _faceMinLikelihood ||
          leftEye.likelihood < _faceMinLikelihood ||
          rightEye.likelihood < _faceMinLikelihood) {
        return null;
      }

      // Decode DOWNSCALED to cap memory (a 12MP photo is ~48MB as raw RGBA;
      // ~720px wide is plenty for colour averaging).
      final bytes = await file.readAsBytes();
      final buffer = await ui.ImmutableBuffer.fromUint8List(bytes);
      final descriptor = await ui.ImageDescriptor.encoded(buffer);
      final int encodedW = descriptor.width, encodedH = descriptor.height;
      final codec = await descriptor.instantiateCodec(targetWidth: 720);
      final frame = await codec.getNextFrame();
      final image = frame.image;
      final w = image.width, h = image.height;
      // Release native decode resources as soon as they're no longer needed.
      codec.dispose();
      descriptor.dispose();
      buffer.dispose();

      // ML Kit landmark coordinates are in the upright original image space.
      // encodedW/H are the ENCODED dimensions, which an EXIF rotation may have
      // swapped relative to the upright frame — match the decoded orientation
      // before computing the scale factor.
      final sameOrientation = (encodedW >= encodedH) == (w >= h);
      final uprightOrigW =
          (sameOrientation ? encodedW : encodedH).toDouble();
      final scale = w / math.max(1.0, uprightOrigW);

      final data = await image.toByteData(format: ui.ImageByteFormat.rawRgba);
      image.dispose();
      if (data == null) return null;
      final px = data.buffer.asUint8List();

      // Face box centred on the (scaled) nose, sized from the inter-eye
      // distance; extended downward to include the cheeks/jaw.
      final noseX = nose.x * scale, noseY = nose.y * scale;
      final eyeDist = ((leftEye.x - rightEye.x).abs() * scale)
          .clamp(4.0, w.toDouble());
      final half = eyeDist * 1.4;
      final x0 = (noseX - half).clamp(0.0, (w - 1).toDouble()).toInt();
      final x1 = (noseX + half).clamp(0.0, (w - 1).toDouble()).toInt();
      final y0 = (noseY - half).clamp(0.0, (h - 1).toDouble()).toInt();
      final y1 = (noseY + half * 1.3).clamp(0.0, (h - 1).toDouble()).toInt();

      // Collect skin pixels, then take the per-channel MEDIAN — robust against
      // specular highlights, lips and stray hair that a mean would absorb.
      final rs = <int>[], gs = <int>[], bs = <int>[];
      final int step = ((x1 - x0) ~/ 40).clamp(1, 8).toInt();
      for (int y = y0; y <= y1; y += step) {
        for (int x = x0; x <= x1; x += step) {
          final i = (y * w + x) * 4;
          final r = px[i], g = px[i + 1], b = px[i + 2];
          if (_isSkin(r, g, b)) {
            rs.add(r);
            gs.add(g);
            bs.add(b);
          }
        }
      }
      if (rs.length < 15) return null; // not enough skin — ask the user

      return _hex(Color.fromARGB(
          255, _median(rs), _median(gs), _median(bs)));
    } catch (_) {
      return null; // any decode/processing failure → manual picker
    }
  }

  int _median(List<int> values) {
    values.sort();
    return values[values.length ~/ 2];
  }

  /// YCbCr skin-colour test (Cb/Cr skin cluster). The luma floor is kept LOW
  /// (y > 20, not the classic 40) so deep skin tones are not excluded — the
  /// classic cluster under-detects dark skin; the median + face box keep the
  /// extra tolerance safe.
  bool _isSkin(int r, int g, int b) {
    final y = 0.299 * r + 0.587 * g + 0.114 * b;
    final cb = 128 - 0.168736 * r - 0.331264 * g + 0.5 * b;
    final cr = 128 + 0.5 * r - 0.418688 * g - 0.081312 * b;
    return y > 20 && cb >= 77 && cb <= 135 && cr >= 133 && cr <= 180;
  }

  // ---------------------------------------------------------------------
  // Seasonal palette classification — a faithful port of the backend's
  // CIELAB logic (backend/app/services/color.py). The server recomputes and
  // stores the authoritative palette from the hex on save; this port exists
  // only so the on-device preview matches what the server will decide.
  // ---------------------------------------------------------------------

  /// sRGB (0-255) -> CIELAB (D65).
  List<double> _labFromRgb(int r, int g, int b) {
    double lin(double c) {
      c /= 255.0;
      return c > 0.04045 ? math.pow((c + 0.055) / 1.055, 2.4).toDouble() : c / 12.92;
    }

    final rl = lin(r.toDouble()), gl = lin(g.toDouble()), bl = lin(b.toDouble());
    final x = rl * 0.4124 + gl * 0.3576 + bl * 0.1805;
    final y = rl * 0.2126 + gl * 0.7152 + bl * 0.0722;
    final z = rl * 0.0193 + gl * 0.1192 + bl * 0.9505;
    const xn = 0.95047, yn = 1.0, zn = 1.08883;

    double f(double t) =>
        t > 0.008856 ? math.pow(t, 1 / 3).toDouble() : (7.787 * t + 16 / 116);

    final fx = f(x / xn), fy = f(y / yn), fz = f(z / zn);
    return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)];
  }

  String _paletteFromHex(String hexStr) {
    final clean = hexStr.replaceAll('#', '');
    final r = int.parse(clean.substring(0, 2), radix: 16);
    final g = int.parse(clean.substring(2, 4), radix: 16);
    final b = int.parse(clean.substring(4, 6), radix: 16);
    final lab = _labFromRgb(r, g, b);
    final l = lab[0], a = lab[1], bb = lab[2];

    final chroma = math.sqrt(a * a + bb * bb);
    final hue = (math.atan2(bb, a) * 180 / math.pi) % 360;
    final ita = bb != 0 ? math.atan2(l - 50.0, bb) * 180 / math.pi : 0.0;

    // Undertone (same thresholds as backend skin_undertone()).
    String undertone;
    if (chroma < 6) {
      undertone = 'neutral';
    } else if (hue >= 57.0) {
      undertone = 'warm';
    } else if (hue <= 46.0) {
      undertone = 'cool';
    } else {
      undertone = 'neutral';
    }

    final isLight = ita > 28.0;
    if (undertone == 'warm') return isLight ? 'warm_spring' : 'warm_autumn';
    if (undertone == 'cool') return isLight ? 'cool_summer' : 'cool_winter';
    return isLight ? 'neutral_light' : 'neutral_deep';
  }

  Future<void> _saveToProfile() async {
    final result = _result;
    if (result == null) return;

    setState(() => _isSaving = true);
    try {
      // ONLY the computed metrics are sent — never the photo. Skin fields are
      // included only when detected or manually chosen. The server recomputes
      // the palette from the hex, so the hex is the value that matters.
      await _apiClient.dio.patch('/users/profile', data: {
        'body_shape': result.bodyShape,
        if (result.skinToneHex != null) 'skin_tone_hex': result.skinToneHex,
        if (result.seasonalPalette != null)
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
                  color: AppColors.error.withOpacity(0.12),
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
        color: AppColors.info.withOpacity(0.12),
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

  /// Manual swatch ladder (fair→deep, warm & cool variants). Used when
  /// detection fails, and always available to correct a detected tone —
  /// the user has the final say (spec Requirement 3.6).
  static const List<String> _skinSwatches = [
    '#FFE0BD', // fair warm
    '#F1C6B5', // fair cool (rosy)
    '#E0AC69', // light golden
    '#C68642', // medium bronze
    '#BB8B7D', // medium cool (mauve)
    '#8D5524', // tan
    '#5C4033', // deep
    '#3B2219', // very deep
  ];

  Color _colorFromHex(String hexStr) =>
      Color(int.parse('FF${hexStr.replaceAll('#', '')}', radix: 16));

  void _selectSwatch(String hexStr) {
    final result = _result;
    if (result == null) return;
    setState(() {
      _result = result.withSkinTone(hexStr, _paletteFromHex(hexStr));
    });
  }

  Widget _buildSwatchPicker(String? selectedHex) {
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: _skinSwatches.map((hexStr) {
        final selected = selectedHex != null &&
            selectedHex.toUpperCase() == hexStr.toUpperCase();
        return GestureDetector(
          onTap: () => _selectSwatch(hexStr),
          child: Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: _colorFromHex(hexStr),
              shape: BoxShape.circle,
              border: Border.all(
                color: selected ? AppColors.primary : AppColors.textMuted,
                width: selected ? 3 : 1,
              ),
            ),
            child: selected
                ? const Icon(Icons.check, size: 18, color: Colors.white)
                : null,
          ),
        );
      }).toList(),
    );
  }

  Widget _buildResultCard(_BodyAnalysisResult result) {
    final hasTone = result.skinToneHex != null;
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
                const Text('Body shape: '),
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
            if (hasTone)
              Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: _colorFromHex(result.skinToneHex!),
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
                        'Palette: ${_prettyPalette(result.seasonalPalette!)}',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ],
              )
            else
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.warning.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Text(
                  'We couldn\'t reliably detect your skin tone from this photo. '
                  'Pick the closest match below.',
                  style: TextStyle(color: AppColors.warning, fontSize: 12),
                ),
              ),
            const SizedBox(height: 12),
            Text(
              hasTone ? 'Not quite right? Adjust:' : 'Choose your skin tone:',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 8),
            _buildSwatchPicker(result.skinToneHex),
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
