// Smoke test for the Style With Us app shell.
//
// Boots the real router app (`StyleWithUsApp`) with `authProvider` overridden
// so the widget tree never touches Firebase in the test environment. Verifies
// the app renders the splash screen and then routes an unauthenticated user to
// the login screen.

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fyp/main.dart';
import 'package:fyp/core/providers/auth_notifier.dart';
import 'package:fyp/features/auth/login_screen.dart';

/// Test double that resolves to "signed out" without calling Firebase.
class _UnauthenticatedAuthNotifier extends AuthNotifier {
  @override
  Future<UserSession?> build() async => null;
}

void main() {
  testWidgets('boots to splash and routes unauthenticated users to login',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWith(_UnauthenticatedAuthNotifier.new),
        ],
        child: const StyleWithUsApp(),
      ),
    );

    // Splash screen renders first.
    expect(find.text('Style With Us'), findsOneWidget);

    // Advance past the splash delay + intro animation; an unauthenticated
    // session is redirected to the login screen.
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();

    expect(find.byType(LoginScreen), findsOneWidget);
  });
}
