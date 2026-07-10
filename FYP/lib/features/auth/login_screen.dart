import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/providers/auth_notifier.dart';
import '../../core/theme.dart';
import '../../shared/widgets/ui.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final authNotifier = ref.read(authProvider.notifier);
      await authNotifier.signIn(
        email: _emailController.text.trim(),
        password: _passwordController.text,
      );

      if (mounted) {
        final role = ref.read(authProvider).value?.role;
        switch (role) {
          case UserRole.brand:
            context.go('/brand');
            break;
          case UserRole.admin:
            context.go('/admin-redirect');
            break;
          default:
            context.go('/shopper');
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
      body: AppBackground(
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(AppSpacing.lg),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: AppSpacing.xl),
                  Center(child: const AppLogo(size: 88))
                      .animate()
                      .fadeIn(duration: 500.ms)
                      .scale(begin: const Offset(0.7, 0.7)),
                  const SizedBox(height: AppSpacing.lg),
                  Text(
                    'Welcome back',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.headlineLarge,
                  ).animate().fadeIn(delay: 150.ms).moveY(begin: 12),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    'Sign in to continue to Style With Us',
                    textAlign: TextAlign.center,
                    style: Theme.of(context)
                        .textTheme
                        .bodyMedium
                        ?.copyWith(color: AppColors.textSecondary),
                  ).animate().fadeIn(delay: 250.ms),
                  const SizedBox(height: AppSpacing.xl),
                  SurfaceCard(
                    padding: const EdgeInsets.all(AppSpacing.lg),
                    child: Column(
                      children: [
                        AppTextField(
                          controller: _emailController,
                          label: 'Email',
                          hint: 'you@example.com',
                          icon: Icons.mail_outline,
                          keyboardType: TextInputType.emailAddress,
                          enabled: !_isLoading,
                        ),
                        const SizedBox(height: AppSpacing.md),
                        AppTextField(
                          controller: _passwordController,
                          label: 'Password',
                          hint: 'Your password',
                          icon: Icons.lock_outline,
                          obscure: true,
                          enabled: !_isLoading,
                        ),
                        if (_errorMessage != null) ...[
                          const SizedBox(height: AppSpacing.md),
                          _ErrorBanner(message: _errorMessage!),
                        ],
                        const SizedBox(height: AppSpacing.lg),
                        GradientButton(
                          label: 'Sign In',
                          icon: Icons.login_rounded,
                          loading: _isLoading,
                          onPressed: _isLoading ? null : _handleLogin,
                        ),
                      ],
                    ),
                  ).animate().fadeIn(delay: 350.ms).moveY(begin: 20),
                  const SizedBox(height: AppSpacing.md),
                  TextButton(
                    onPressed: _isLoading ? null : () => context.go('/signup'),
                    child: const Text("Don't have an account? Sign up"),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  final String message;
  const _ErrorBanner({required this.message});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(AppSpacing.sm + 4),
      decoration: BoxDecoration(
        color: AppColors.error.withOpacity(0.12),
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: AppColors.error.withOpacity(0.4)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: AppColors.error, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(message,
                style: const TextStyle(color: AppColors.error, fontSize: 13)),
          ),
        ],
      ),
    ).animate().shake(hz: 3, curve: Curves.easeInOut);
  }
}

String _friendlyError(Object e) {
  final s = e.toString().toLowerCase();
  if (s.contains('password') || s.contains('credential')) {
    return 'Incorrect email or password.';
  }
  if (s.contains('user-not-found') || s.contains('no user')) {
    return 'No account found with that email.';
  }
  if (s.contains('network')) return 'Network error. Check your connection.';
  return 'Sign in failed. Please try again.';
}
