import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/providers/auth_notifier.dart';
import '../../core/theme.dart';
import '../../shared/widgets/ui.dart';

class SignupScreen extends ConsumerStatefulWidget {
  const SignupScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends ConsumerState<SignupScreen> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _companyNameController = TextEditingController();

  String _selectedRole = 'shopper';
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _companyNameController.dispose();
    super.dispose();
  }

  Future<void> _handleSignup() async {
    if (_passwordController.text != _confirmPasswordController.text) {
      setState(() => _errorMessage = 'Passwords do not match');
      return;
    }
    if (_selectedRole == 'brand' && _companyNameController.text.trim().isEmpty) {
      setState(() => _errorMessage = 'Please enter your company name');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final authNotifier = ref.read(authProvider.notifier);
      await authNotifier.signUp(
        email: _emailController.text.trim(),
        password: _passwordController.text,
        name: _nameController.text.trim(),
        role: _selectedRole,
        companyName:
            _selectedRole == 'brand' ? _companyNameController.text.trim() : null,
      );

      if (mounted) {
        if (_selectedRole == 'shopper') {
          context.go('/profile-setup');
        } else {
          context.go('/$_selectedRole');
        }
      }
    } catch (e) {
      setState(() => _errorMessage = _friendlyError(e));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(backgroundColor: Colors.transparent),
      extendBodyBehindAppBar: true,
      body: AppBackground(
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Center(child: const AppLogo(size: 72))
                    .animate()
                    .fadeIn(duration: 500.ms)
                    .scale(begin: const Offset(0.7, 0.7)),
                const SizedBox(height: AppSpacing.md),
                Text(
                  'Create your account',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headlineMedium,
                ).animate().fadeIn(delay: 150.ms).moveY(begin: 12),
                const SizedBox(height: AppSpacing.lg),
                SurfaceCard(
                  padding: const EdgeInsets.all(AppSpacing.lg),
                  child: Column(
                    children: [
                      _RoleSelector(
                        value: _selectedRole,
                        onChanged: _isLoading
                            ? null
                            : (v) => setState(() => _selectedRole = v),
                      ),
                      const SizedBox(height: AppSpacing.md),
                      AppTextField(
                        controller: _nameController,
                        label: 'Full Name',
                        icon: Icons.person_outline,
                        enabled: !_isLoading,
                      ),
                      const SizedBox(height: AppSpacing.md),
                      if (_selectedRole == 'brand') ...[
                        AppTextField(
                          controller: _companyNameController,
                          label: 'Company Name',
                          icon: Icons.storefront_outlined,
                          enabled: !_isLoading,
                        ).animate().fadeIn().moveY(begin: -8),
                        const SizedBox(height: AppSpacing.md),
                      ],
                      AppTextField(
                        controller: _emailController,
                        label: 'Email',
                        icon: Icons.mail_outline,
                        keyboardType: TextInputType.emailAddress,
                        enabled: !_isLoading,
                      ),
                      const SizedBox(height: AppSpacing.md),
                      AppTextField(
                        controller: _passwordController,
                        label: 'Password',
                        icon: Icons.lock_outline,
                        obscure: true,
                        enabled: !_isLoading,
                      ),
                      const SizedBox(height: AppSpacing.md),
                      AppTextField(
                        controller: _confirmPasswordController,
                        label: 'Confirm Password',
                        icon: Icons.lock_outline,
                        obscure: true,
                        enabled: !_isLoading,
                      ),
                      if (_errorMessage != null) ...[
                        const SizedBox(height: AppSpacing.md),
                        AppErrorBanner(message: _errorMessage!),
                      ],
                      const SizedBox(height: AppSpacing.lg),
                      GradientButton(
                        label: 'Create Account',
                        icon: Icons.person_add_alt_1_rounded,
                        loading: _isLoading,
                        onPressed: _isLoading ? null : _handleSignup,
                      ),
                    ],
                  ),
                ).animate().fadeIn(delay: 300.ms).moveY(begin: 20),
                const SizedBox(height: AppSpacing.md),
                TextButton(
                  onPressed: _isLoading ? null : () => context.go('/login'),
                  child: const Text('Already have an account? Login'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _RoleSelector extends StatelessWidget {
  final String value;
  final ValueChanged<String>? onChanged;
  const _RoleSelector({required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        _tile(context, 'shopper', 'Shopper', Icons.shopping_bag_outlined),
        const SizedBox(width: AppSpacing.sm),
        _tile(context, 'brand', 'Brand', Icons.storefront_outlined),
      ],
    );
  }

  Widget _tile(BuildContext context, String v, String label, IconData icon) {
    final selected = value == v;
    return Expanded(
      child: GestureDetector(
        onTap: onChanged == null ? null : () => onChanged!(v),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(vertical: 16),
          decoration: BoxDecoration(
            gradient: selected ? AppColors.gradientPrimary : null,
            color: selected ? null : AppColors.bgElevated,
            borderRadius: BorderRadius.circular(AppRadius.md),
            border: Border.all(
              color: selected ? Colors.transparent : AppColors.border,
            ),
          ),
          child: Column(
            children: [
              Icon(icon,
                  color: selected ? Colors.white : AppColors.textSecondary),
              const SizedBox(height: 6),
              Text(
                label,
                style: TextStyle(
                  color: selected ? Colors.white : AppColors.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

String _friendlyError(Object e) {
  final s = e.toString().toLowerCase();
  if (s.contains('email-already-in-use') || s.contains('already in use')) {
    return 'An account with that email already exists.';
  }
  if (s.contains('weak-password') || s.contains('at least 6')) {
    return 'Password should be at least 6 characters.';
  }
  if (s.contains('invalid-email')) return 'Please enter a valid email address.';
  if (s.contains('network')) return 'Network error. Check your connection.';
  return 'Could not create your account. Please try again.';
}
