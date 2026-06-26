import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/providers/profile_setup_notifier.dart';

class ProfileSetupScreen extends ConsumerStatefulWidget {
  const ProfileSetupScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<ProfileSetupScreen> createState() => _ProfileSetupScreenState();
}

class _ProfileSetupScreenState extends ConsumerState<ProfileSetupScreen> {
  int _currentStep = 0;
  bool _isLoading = false;
  String? _errorMessage;

  final _heightController = TextEditingController();
  final _weightController = TextEditingController();
  final _ageController = TextEditingController();
  final _chestController = TextEditingController();
  final _waistController = TextEditingController();
  final _hipsController = TextEditingController();
  final _inseamController = TextEditingController();
  final _shoulderController = TextEditingController();

  @override
  void dispose() {
    _heightController.dispose();
    _weightController.dispose();
    _ageController.dispose();
    _chestController.dispose();
    _waistController.dispose();
    _hipsController.dispose();
    _inseamController.dispose();
    _shoulderController.dispose();
    super.dispose();
  }

  Future<void> _handleNext() async {
    if (_currentStep == 0) {
      // Gender step - validate
      final profile = ref.read(profileSetupProvider);
      if (profile.gender == null) {
        setState(() => _errorMessage = 'Please select your gender');
        return;
      }
    }

    if (_currentStep < 3) {
      setState(() {
        _currentStep++;
        _errorMessage = null;
      });
    } else {
      await _submitProfile();
    }
  }

  Future<void> _submitProfile() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // Parse and set all values
      final profile = ref.read(profileSetupProvider.notifier);

      if (_heightController.text.isNotEmpty) {
        profile.setHeight(double.parse(_heightController.text));
      }
      if (_weightController.text.isNotEmpty) {
        profile.setWeight(double.parse(_weightController.text));
      }
      if (_ageController.text.isNotEmpty) {
        profile.setAge(int.parse(_ageController.text));
      }
      if (_chestController.text.isNotEmpty) {
        profile.setChest(double.parse(_chestController.text));
      }
      if (_waistController.text.isNotEmpty) {
        profile.setWaist(double.parse(_waistController.text));
      }
      if (_hipsController.text.isNotEmpty) {
        profile.setHips(double.parse(_hipsController.text));
      }
      if (_inseamController.text.isNotEmpty) {
        profile.setInseam(double.parse(_inseamController.text));
      }
      if (_shoulderController.text.isNotEmpty) {
        profile.setShoulderWidth(double.parse(_shoulderController.text));
      }

      await profile.submitProfile();

      if (mounted) {
        context.go('/shopper');
      }
    } catch (e) {
      setState(() => _errorMessage = e.toString());
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final profile = ref.watch(profileSetupProvider);
    final unitIsCm = profile.unitPreference == UnitPreference.metric;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Set Up Your Profile'),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Step indicator
            Row(
              children: List.generate(4, (i) => Expanded(
                child: Container(
                  height: 4,
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  decoration: BoxDecoration(
                    color: i <= _currentStep ? Colors.blue : Colors.grey.shade300,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              )),
            ),
            const SizedBox(height: 32),

            // Step 0: Gender
            if (_currentStep == 0) ...[
              Text('Step 0: Select Your Gender',
                style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 24),
              _buildGenderSelector(ref),
            ],

            // Step 1: Units
            if (_currentStep == 1) ...[
              Text('Step 1: Measurement Units',
                style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 24),
              SegmentedButton<UnitPreference>(
                segments: const [
                  ButtonSegment(label: Text('Metric (cm/kg)'), value: UnitPreference.metric),
                  ButtonSegment(label: Text('Imperial (in/lbs)'), value: UnitPreference.imperial),
                ],
                selected: {profile.unitPreference},
                onSelectionChanged: (Set<UnitPreference> newSelection) {
                  ref.read(profileSetupProvider.notifier)
                    .setUnitPreference(newSelection.first);
                },
              ),
            ],

            // Step 2: Basic Stats
            if (_currentStep == 2) ...[
              Text('Step 2: Basic Information',
                style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: () => context.push('/shopper/body-analysis'),
                icon: const Icon(Icons.camera_alt),
                label: const Text('Auto-fill with AI Camera'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.blue,
                  side: const BorderSide(color: Colors.blue),
                ),
              ),
              const SizedBox(height: 24),
              TextField(
                controller: _heightController,
                decoration: InputDecoration(
                  labelText: unitIsCm ? 'Height (cm)' : 'Height (inches)',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _weightController,
                decoration: InputDecoration(
                  labelText: unitIsCm ? 'Weight (kg)' : 'Weight (lbs)',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _ageController,
                decoration: InputDecoration(
                  labelText: 'Age',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
                keyboardType: TextInputType.number,
              ),
            ],

            // Step 3: Body Measurements
            if (_currentStep == 3) ...[
              Text('Step 3: Body Measurements',
                style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 24),
              TextField(
                controller: _chestController,
                decoration: InputDecoration(
                  labelText: unitIsCm ? 'Chest (cm)' : 'Chest (inches)',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _waistController,
                decoration: InputDecoration(
                  labelText: unitIsCm ? 'Waist (cm)' : 'Waist (inches)',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _hipsController,
                decoration: InputDecoration(
                  labelText: unitIsCm ? 'Hips (cm)' : 'Hips (inches)',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _inseamController,
                decoration: InputDecoration(
                  labelText: unitIsCm ? 'Inseam (cm)' : 'Inseam (inches)',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _shoulderController,
                decoration: InputDecoration(
                  labelText: unitIsCm ? 'Shoulder Width (cm)' : 'Shoulder Width (inches)',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
                keyboardType: TextInputType.number,
              ),
            ],

            if (_errorMessage != null) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(_errorMessage!,
                  style: TextStyle(color: Colors.red.shade700)),
              ),
            ],

            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: _isLoading ? null : _handleNext,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: _isLoading
                  ? const SizedBox(
                      height: 20, width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Text(_currentStep == 3 ? 'Complete' : 'Next'),
            ),
            const SizedBox(height: 16),
            if (_currentStep > 0)
              OutlinedButton(
                onPressed: _isLoading
                    ? null
                    : () => setState(() => _currentStep--),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text('Back'),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildGenderSelector(WidgetRef ref) {
    final profile = ref.watch(profileSetupProvider);
    final genders = ['Male', 'Female', 'Non-binary'];

    return Column(
      children: genders.map((gender) {
        final isSelected = profile.gender == gender.toLowerCase();
        return Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: ElevatedButton(
            onPressed: () {
              ref.read(profileSetupProvider.notifier)
                .setGender(gender.toLowerCase());
            },
            style: ElevatedButton.styleFrom(
              backgroundColor:
                  isSelected ? Colors.blue : Colors.grey.shade200,
              foregroundColor: isSelected ? Colors.white : Colors.black,
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
            child: Text(gender, style: const TextStyle(fontSize: 16)),
          ),
        );
      }).toList(),
    );
  }
}
