import 'dart:io';
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:camera/camera.dart';
import 'package:go_router/go_router.dart';
import '../../core/providers/cart_notifier.dart';
import 'package:google_mlkit_pose_detection/google_mlkit_pose_detection.dart';

class ARTryOnScreen extends ConsumerStatefulWidget {
  const ARTryOnScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<ARTryOnScreen> createState() => _ARTryOnScreenState();
}

class _ARTryOnScreenState extends ConsumerState<ARTryOnScreen> {
  late CameraController _cameraController;
  bool _isCameraInitialized = false;
  bool _noPoseDetected = false;
  int _noPoseCounter = 0;
  String? _selectedGarmentId;
  Timer? _poseTimer;

  final PoseDetector _poseDetector = PoseDetector(options: PoseDetectorOptions());
  bool _isDetecting = false;
  Pose? _currentPose;

  final List<Map<String, String>> _garments = [
    {
      'id': 'garment-1',
      'name': 'Blue T-Shirt',
      'image': '👕',
    },
    {
      'id': 'garment-2',
      'name': 'Red Jacket',
      'image': '🧥',
    },
    {
      'id': 'garment-3',
      'name': 'Black Pants',
      'image': '👖',
    },
  ];

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      final frontCamera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );

      _cameraController = CameraController(
        frontCamera,
        ResolutionPreset.high,
      );

      await _cameraController.initialize();

      if (mounted) {
        setState(() {
          _isCameraInitialized = true;
        });
      }

      _startPoseDetection();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Camera error: $e')),
      );
    }
  }

  void _startPoseDetection() {
    _cameraController.startImageStream((CameraImage image) async {
      if (_isDetecting) return;
      _isDetecting = true;

      try {
        final inputImage = _inputImageFromCameraImage(image);
        if (inputImage == null) return;

        final poses = await _poseDetector.processImage(inputImage);

        if (mounted) {
          if (poses.isEmpty) {
            _noPoseCounter++;
            if (_noPoseCounter > 10) { // Approx 1 second
              setState(() {
                _noPoseDetected = true;
                _currentPose = null;
              });
            }
          } else {
            _noPoseCounter = 0;
            setState(() {
              _noPoseDetected = false;
              _currentPose = poses.first;
            });
          }
        }
      } catch (e) {
        print('Pose detection error: ' + e.toString());
      } finally {
        _isDetecting = false;
      }
    });
  }

  InputImage? _inputImageFromCameraImage(CameraImage image) {
    // Basic image format handling for Google ML Kit
    final camera = _cameraController.description;
    final sensorOrientation = camera.sensorOrientation;

    InputImageRotation? rotation;
    if (Platform.isIOS) {
      rotation = InputImageRotationValue.fromRawValue(sensorOrientation);
    } else if (Platform.isAndroid) {
      var rotationCompensation = _cameraController.value.deviceOrientation.index * 90;
      if (camera.lensDirection == CameraLensDirection.front) {
        rotationCompensation = (sensorOrientation + rotationCompensation) % 360;
      } else {
        rotationCompensation = (sensorOrientation - rotationCompensation + 360) % 360;
      }
      rotation = InputImageRotationValue.fromRawValue(rotationCompensation);
    }
    if (rotation == null) return null;

    final format = InputImageFormatValue.fromRawValue(image.format.raw);
    if (format == null) return null;

    final plane = image.planes.first;

    return InputImage.fromBytes(
      bytes: plane.bytes,
      metadata: InputImageMetadata(
        size: Size(image.width.toDouble(), image.height.toDouble()),
        rotation: rotation,
        format: format,
        bytesPerRow: plane.bytesPerRow,
      ),
    );
  }

  void _selectGarment(String garmentId) {
    setState(() {
      _selectedGarmentId = garmentId;
      _noPoseDetected = false;
    });
  }

  void _addToCart() {
    if (_selectedGarmentId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a garment first')),
      );
      return;
    }

    ref.read(cartProvider.notifier).addItem(
      _selectedGarmentId!,
      _garments
          .firstWhere((g) => g['id'] == _selectedGarmentId)['name']!,
      89.99,
      sizeSpecId: 'spec-1',
      sizeLabel: 'M',
    );

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
  void dispose() {
    _poseTimer?.cancel();
    _cameraController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AR Try-On'),
        centerTitle: true,
      ),
      body: _isCameraInitialized
          ? Stack(
              children: [
                // Camera preview
                CameraPreview(_cameraController),

                // Garment overlay using ML Kit Pose Detection
                if (_selectedGarmentId != null && _currentPose != null)
                  CustomPaint(
                    painter: GarmentOverlayPainter(
                      pose: _currentPose!,
                      garmentEmoji: _garments.firstWhere((g) => g['id'] == _selectedGarmentId)['image']!,
                      imageSize: Size(
                        _cameraController.value.previewSize?.height ?? 1,
                        _cameraController.value.previewSize?.width ?? 1,
                      ),
                      screenSize: MediaQuery.of(context).size,
                      lensDirection: _cameraController.description.lensDirection,
                    ),
                  ),

                // No pose indicator
                if (_noPoseDetected)
                  Positioned(
                    top: 20,
                    left: 20,
                    right: 20,
                    child: Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.orange.shade700,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.warning, color: Colors.white),
                          const SizedBox(width: 12),
                          const Expanded(
                            child: Text(
                              'Step back for a full-body view',
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                // Garment selector at bottom
                Positioned(
                  bottom: 0,
                  left: 0,
                  right: 0,
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.7),
                      borderRadius: const BorderRadius.only(
                        topLeft: Radius.circular(12),
                        topRight: Radius.circular(12),
                      ),
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Padding(
                          padding: const EdgeInsets.all(12),
                          child: Text(
                            'Select Garment',
                            style: Theme.of(context).textTheme.titleMedium
                                ?.copyWith(color: Colors.white),
                          ),
                        ),
                        SizedBox(
                          height: 120,
                          child: ListView.builder(
                            scrollDirection: Axis.horizontal,
                            padding: const EdgeInsets.symmetric(horizontal: 12),
                            itemCount: _garments.length,
                            itemBuilder: (context, index) {
                              final garment = _garments[index];
                              final isSelected =
                                  _selectedGarmentId == garment['id'];

                              return GestureDetector(
                                onTap: () => _selectGarment(garment['id']!),
                                child: Container(
                                  width: 100,
                                  margin: const EdgeInsets.only(right: 8),
                                  decoration: BoxDecoration(
                                    color: isSelected
                                        ? Colors.blue
                                        : Colors.grey.shade700,
                                    borderRadius: BorderRadius.circular(8),
                                    border: isSelected
                                        ? Border.all(
                                            color: Colors.lightBlue,
                                            width: 3,
                                          )
                                        : null,
                                  ),
                                  child: Column(
                                    mainAxisAlignment:
                                        MainAxisAlignment.center,
                                    children: [
                                      Text(
                                        garment['image']!,
                                        style: const TextStyle(fontSize: 40),
                                      ),
                                      const SizedBox(height: 8),
                                      Text(
                                        garment['name']!,
                                        textAlign: TextAlign.center,
                                        style: const TextStyle(
                                          color: Colors.white,
                                          fontSize: 11,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              );
                            },
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.all(12),
                          child: Row(
                            children: [
                              Expanded(
                                child: OutlinedButton(
                                  onPressed: () => context.go('/shopper'),
                                  child: const Text('Back'),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: ElevatedButton(
                                  onPressed: _addToCart,
                                  child: const Text('Add to Cart'),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            )
          : const Center(
              child: CircularProgressIndicator(),
            ),
    );
  }
}


class GarmentOverlayPainter extends CustomPainter {
  final Pose pose;
  final String garmentEmoji;
  final Size imageSize;
  final Size screenSize;
  final CameraLensDirection lensDirection;

  GarmentOverlayPainter({
    required this.pose,
    required this.garmentEmoji,
    required this.imageSize,
    required this.screenSize,
    required this.lensDirection,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final leftShoulder = pose.landmarks[PoseLandmarkType.leftShoulder];
    final rightShoulder = pose.landmarks[PoseLandmarkType.rightShoulder];
    final leftHip = pose.landmarks[PoseLandmarkType.leftHip];

    if (leftShoulder == null || rightShoulder == null || leftHip == null) return;

    // Transform points to screen space
    final double scaleX = screenSize.width / imageSize.width;
    final double scaleY = screenSize.height / imageSize.height;

    double transformX(double x) {
      if (lensDirection == CameraLensDirection.front) {
        return screenSize.width - (x * scaleX);
      }
      return x * scaleX;
    }

    double transformY(double y) {
      return y * scaleY;
    }

    final lsX = transformX(leftShoulder.x);
    final lsY = transformY(leftShoulder.y);
    final rsX = transformX(rightShoulder.x);
    final rsY = transformY(rightShoulder.y);
    final lhY = transformY(leftHip.y);

    final centerX = (lsX + rsX) / 2;
    final centerY = (lsY + rsY) / 2;
    final garmentWidth = (lsX - rsX).abs() * 2.5; // Roughly 2.5x shoulder width
    final garmentHeight = (lhY - centerY).abs() * 1.5;

    final textPainter = TextPainter(
      text: TextSpan(text: garmentEmoji, style: TextStyle(fontSize: garmentHeight)),
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();

    // Center the emoji on the torso
    final drawPosition = Offset(
      centerX - (textPainter.width / 2),
      centerY,
    );

    textPainter.paint(canvas, drawPosition);
  }

  @override
  bool shouldRepaint(covariant GarmentOverlayPainter oldDelegate) {
    return oldDelegate.pose != pose || oldDelegate.garmentEmoji != garmentEmoji;
  }
}