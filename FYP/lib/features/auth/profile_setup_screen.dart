import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/providers/profile_setup_notifier.dart';
import '../../core/theme.dart';
import '../../shared/widgets/ui.dart';

class ProfileSetupScreen extends ConsumerStatefulWidget {
  const ProfileSetupScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<ProfileSetupScreen> createState() => _ProfileSetupScreenState();
}

class _ProfileSetupScreenState extends ConsumerState<ProfileSetupScreen> {
  int _currentStep = 0;
  bool _isLoading = false;
  String? _errorMessage;

  static const _titles = [
    'Your gender',
    'Measurement units',
    'Basic information',
    'Body measurements',
  ];
  static const _subtitles = [
    'Required — we use it to show relevant styles.',
    'Choose the units you prefer to enter.',
    'Optional — helps size recommendations.',
    'Optional — for precise fit matching.',
  ];

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
      final profile = ref.read(profileSetupProvider.notifier);
      final isImperial = ref.read(profileSetupProvider).unitPreference ==
          UnitPreference.imperial;
      double toCm(double v) => isImperial ? v * 2.54 : v;
      double toKg(double v) => isImperial ? v * 0.45359237 : v;

      if (_heightController.text.isNotEmpty) {
        profile.setHeight(toCm(double.parse(_heightController.text)));
      }
      if (_weightController.text.isNotEmpty) {
        profile.setWeight(toKg(double.parse(_weightController.text)));
      }
      if (_ageController.text.isNotEmpty) {
        profile.setAge(int.parse(_ageController.text));
      }
      if (_chestController.text.isNotEmpty) {
        profile.setChest(toCm(double.parse(_chestController.text)));
      }
      if (_waistController.text.isNotEmpty) {
        profile.setWaist(toCm(double.parse(_waistController.text)));
      }
      if (_hipsController.text.isNotEmpty) {
        profile.setHips(toCm(double.parse(_hipsController.text)));
      }
      if (_inseamController.text.isNotEmpty) {
        profile.setInseam(toCm(double.parse(_inseamController.text)));
      }
      if (_shoulderController.text.isNotEmpty) {
        profile.setShoulderWidth(toCm(double.parse(_shoulderController.text)));
      }

      await profile.submitProfile();
      if (mounted) context.go('/shopper');
    } catch (e) {
      setState(() => _errorMessage = 'Could not save your profile. Try again.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final profile = ref.watch(profileSetupProvider);
    final unitIsCm = profile.unitPreference == UnitPreference.metric;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Set Up Your Profile'),
        backgroundColor: Colors.transparent,
      ),
      body: AppBackground(
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Progress bar
                Row(
                  children: List.generate(
                    4,
                    (i) => Expanded(
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 250),
                        height: 5,
                        margin: const EdgeInsets.symmetric(horizontal: 3),
                        decoration: BoxDecoration(
                          gradient: i <= _currentStep
                              ? AppColors.gradientPrimary
                              : null,
                          color:
                              i <= _currentStep ? null : AppColors.bgElevated,
                          borderRadius: BorderRadius.circular(3),
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.xs),
                Text('Step ${_currentStep + 1} of 4',
                    style: Theme.of(context)
                        .textTheme
                        .bodySmall
                        ?.copyWith(color: AppColors.textMuted)),
                const SizedBox(height: AppSpacing.lg),
                Text(_titles[_currentStep],
                    style: Theme.of(context).textTheme.headlineMedium),
                const SizedBox(height: AppSpacing.xs),
                Text(_subtitles[_currentStep],
                    style: Theme.of(context)
                        .textTheme
                        .bodyMedium
                        ?.copyWith(color: AppColors.textSecondary)),
                const SizedBox(height: AppSpacing.lg),

                // Animated step body
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 250),
                  child: KeyedSubtree(
                    key: ValueKey(_currentStep),
                    child: _buildStep(context, unitIsCm),
                  ),
                ),

                if (_errorMessage != null) ...[
                  const SizedBox(height: AppSpacing.md),
                  AppErrorBanner(message: _errorMessage!),
                ],

                const SizedBox(height: AppSpacing.xl),
                GradientButton(
                  label: _currentStep == 3 ? 'Complete Setup' : 'Continue',
                  icon: _currentStep == 3
                      ? Icons.check_rounded
                      : Icons.arrow_forward_rounded,
                  loading: _isLoading,
                  onPressed: _isLoading ? null : _handleNext,
                ),
                const SizedBox(height: AppSpacing.sm),
                if (_currentStep > 0)
                  TextButton(
                    onPressed: _isLoading
                        ? null
                        : () => setState(() => _currentStep--),
                    child: const Text('Back'),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStep(BuildContext context, bool unitIsCm) {
    switch (_currentStep) {
      case 0:
        return _buildGenderSelector();
      case 1:
        final profile = ref.watch(profileSetupProvider);
        return Row(
          children: [
            _unitTile('Metric', 'cm · kg', UnitPreference.metric,
                profile.unitPreference),
            const SizedBox(width: AppSpacing.sm),
            _unitTile('Imperial', 'in · lbs', UnitPreference.imperial,
                profile.unitPreference),
          ],
        );
      case 2:
        return SurfaceCard(
          child: Column(
            children: [
              OutlinedButton.icon(
                onPressed: () => context.push('/shopper/body-analysis'),
                icon: const Icon(Icons.auto_awesome),
                label: const Text('Auto-fill with AI Camera'),
              ),
              const SizedBox(height: AppSpacing.md),
              AppTextField(
                controller: _heightController,
                label: unitIsCm ? 'Height (cm)' : 'Height (inches)',
                icon: Icons.height,
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: AppSpacing.md),
              AppTextField(
                controller: _weightController,
                label: unitIsCm ? 'Weight (kg)' : 'Weight (lbs)',
                icon: Icons.monitor_weight_outlined,
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: AppSpacing.md),
              AppTextField(
                controller: _ageController,
                label: 'Age',
                icon: Icons.cake_outlined,
                keyboardType: TextInputType.number,
              ),
            ],
          ),
        );
      default:
        return SurfaceCard(
          child: Column(
            children: [
              for (final f in [
                [_chestController, 'Chest'],
                [_waistController, 'Waist'],
                [_hipsController, 'Hips'],
                [_inseamController, 'Inseam'],
                [_shoulderController, 'Shoulder Width'],
              ]) ...[
                AppTextField(
                  controller: f[0] as TextEditingController,
                  label:
                      '${f[1]} (${unitIsCm ? 'cm' : 'inches'})',
                  icon: Icons.straighten,
                  keyboardType: TextInputType.number,
                ),
                const SizedBox(height: AppSpacing.md),
              ],
            ],
          ),
        );
    }
  }

  Widget _unitTile(
      String label, String sub, UnitPreference v, UnitPreference current) {
    final selected = v == current;
    return Expanded(
      child: GestureDetector(
        onTap: () =>
            ref.read(profileSetupProvider.notifier).setUnitPreference(v),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(vertical: AppSpacing.lg),
          decoration: BoxDecoration(
            gradient: selected ? AppColors.gradientPrimary : null,
            color: selected ? null : AppColors.bgCard,
            borderRadius: BorderRadius.circular(AppRadius.lg),
            border: Border.all(
                color: selected ? Colors.transparent : AppColors.border),
          ),
          child: Column(
            children: [
              Text(label,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    color: selected ? Colors.white : AppColors.textPrimary,
                  )),
              const SizedBox(height: 4),
              Text(sub,
                  style: TextStyle(
                    color:
                        selected ? Colors.white70 : AppColors.textSecondary,
                  )),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildGenderSelector() {
    final profile = ref.watch(profileSetupProvider);
    const genders = {
      'Male': ['male', Icons.male],
      'Female': ['female', Icons.female],
      'Non-binary': ['non_binary', Icons.transgender],
    };
    return Column(
      children: genders.entries.map((entry) {
        final value = entry.value[0] as String;
        final icon = entry.value[1] as IconData;
        final selected = profile.gender == value;
        return Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.md),
          child: GestureDetector(
            onTap: () =>
                ref.read(profileSetupProvider.notifier).setGender(value),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              padding: const EdgeInsets.all(AppSpacing.md),
              decoration: BoxDecoration(
                gradient: selected ? AppColors.gradientPrimary : null,
                color: selected ? null : AppColors.bgCard,
                borderRadius: BorderRadius.circular(AppRadius.lg),
                border: Border.all(
                    color: selected ? Colors.transparent : AppColors.border),
              ),
              child: Row(
                children: [
                  Icon(icon,
                      color:
                          selected ? Colors.white : AppColors.primaryLight),
                  const SizedBox(width: AppSpacing.md),
                  Text(entry.key,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color:
                            selected ? Colors.white : AppColors.textPrimary,
                      )),
                  const Spacer(),
                  if (selected)
                    const Icon(Icons.check_circle, color: Colors.white),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}
