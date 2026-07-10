import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/providers/auth_notifier.dart';
import '../../core/theme.dart';
import '../../shared/widgets/ui.dart';

class AdminRedirectScreen extends ConsumerWidget {
  const AdminRedirectScreen({Key? key}) : super(key: key);

  static const String adminPortalUrl = 'http://localhost:5173/admin/';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin Portal'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(authProvider.notifier).signOut(),
            tooltip: 'Logout',
          ),
        ],
      ),
      body: AppBackground(
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(AppSpacing.lg),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const AppLogo(size: 84)
                      .animate()
                      .fadeIn()
                      .scale(begin: const Offset(0.7, 0.7)),
                  const SizedBox(height: AppSpacing.lg),
                  Text('Admin Portal',
                      style: Theme.of(context).textTheme.headlineMedium),
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    'Administrative tools live on the web portal.',
                    textAlign: TextAlign.center,
                    style: Theme.of(context)
                        .textTheme
                        .bodyMedium
                        ?.copyWith(color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  SurfaceCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Portal URL',
                            style: Theme.of(context).textTheme.titleMedium),
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            Expanded(
                              child: SelectableText(
                                adminPortalUrl,
                                style: const TextStyle(
                                    fontFamily: 'monospace',
                                    color: AppColors.primaryLight),
                              ),
                            ),
                            IconButton(
                              icon: const Icon(Icons.copy, size: 18),
                              onPressed: () async {
                                await Clipboard.setData(const ClipboardData(
                                    text: adminPortalUrl));
                                if (context.mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                        content: Text('URL copied')),
                                  );
                                }
                              },
                            ),
                          ],
                        ),
                        Divider(color: AppColors.border, height: 24),
                        Text('Features',
                            style: Theme.of(context).textTheme.titleMedium),
                        const SizedBox(height: 8),
                        for (final f in const [
                          'Real-time analytics dashboard',
                          'User & role management',
                          'Brand management',
                          'ML job queue monitoring',
                          'Sales reports',
                        ])
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 3),
                            child: Row(
                              children: [
                                const Icon(Icons.check_circle_outline,
                                    size: 16, color: AppColors.success),
                                const SizedBox(width: 8),
                                Text(f),
                              ],
                            ),
                          ),
                      ],
                    ),
                  ).animate().fadeIn(delay: 150.ms).moveY(begin: 16),
                  const SizedBox(height: AppSpacing.lg),
                  GradientButton(
                    label: 'Copy Portal URL',
                    icon: Icons.copy_all_rounded,
                    onPressed: () async {
                      await Clipboard.setData(
                          const ClipboardData(text: adminPortalUrl));
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('URL copied to clipboard')),
                        );
                      }
                    },
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  TextButton(
                    onPressed: () => context.go('/'),
                    child: const Text('Return to Home'),
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
