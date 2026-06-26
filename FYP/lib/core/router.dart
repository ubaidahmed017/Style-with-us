import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'providers/auth_notifier.dart';
import '../features/auth/login_screen.dart';
import '../features/auth/signup_screen.dart';
import '../features/auth/profile_setup_screen.dart';
import '../features/splash/splash_screen.dart';
import '../features/shopper/home_screen.dart';
import '../features/shopper/product_detail_screen.dart';
import '../features/shopper/virtual_tryon_screen.dart';
import '../features/shopper/ar_tryon_screen.dart';
import '../features/shopper/body_analysis_screen.dart';
import '../features/shopper/checkout_screen.dart';
import '../features/shopper/order_history_screen.dart';
import '../features/shopper/wishlist_screen.dart';
import '../shared/models/product_model.dart';
import '../features/brand/brand_dashboard_screen.dart';
import '../features/brand/brand_products_screen.dart';
import '../features/brand/brand_analytics_screen.dart';
import '../features/brand/product_upload_screen.dart';
import '../features/admin/admin_redirect_screen.dart';

final routerProvider = Provider((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final isAuthenticated = authState.when(
        data: (user) => user != null,
        loading: () => false,
        error: (_, __) => false,
      );

      final isSplash = state.matchedLocation == '/';
      final isLoggingIn = state.matchedLocation == '/login' ||
          state.matchedLocation == '/signup';

      if (!isAuthenticated && !isLoggingIn && !isSplash) {
        return '/login';
      }

      if (isAuthenticated && isLoggingIn) {
        return _getHomeRoute(authState);
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/signup',
        builder: (context, state) => const SignupScreen(),
      ),
      GoRoute(
        path: '/profile-setup',
        builder: (context, state) => const ProfileSetupScreen(),
      ),
      GoRoute(
        path: '/shopper',
        builder: (context, state) => const ShopperHomeScreen(),
        routes: [
          GoRoute(
            path: 'product/:id',
            builder: (context, state) {
              final productId = state.pathParameters['id']!;
              final product = state.extra as Product?;
              return ProductDetailScreen(productId: productId, product: product);
            },
          ),
          GoRoute(
            path: 'orders',
            builder: (context, state) => const OrderHistoryScreen(),
          ),
          GoRoute(
            path: 'wishlist',
            builder: (context, state) => const WishlistScreen(),
          ),
          GoRoute(
            path: 'try-on',
            builder: (context, state) {
              final product = state.extra as Product?;
              return VirtualTryOnScreen(product: product);
            },
          ),
          GoRoute(
            path: 'ar-tryon',
            builder: (context, state) => const ARTryOnScreen(),
          ),
          GoRoute(
            path: 'checkout',
            builder: (context, state) => const CheckoutScreen(),
          ),
          GoRoute(
            path: 'body-analysis',
            builder: (context, state) => const BodyAnalysisScreen(),
          ),
        ],
      ),
      GoRoute(
        path: '/brand',
        builder: (context, state) => const BrandDashboardScreen(),
        routes: [
          GoRoute(
            path: 'products',
            builder: (context, state) => const BrandProductsScreen(),
          ),
          GoRoute(
            path: 'upload',
            builder: (context, state) => const ProductUploadScreen(),
          ),
          GoRoute(
            path: 'analytics',
            builder: (context, state) => const BrandAnalyticsScreen(),
          ),
        ],
      ),
      GoRoute(
        path: '/admin-redirect',
        builder: (context, state) => const AdminRedirectScreen(),
      ),
    ],
  );
});

String _getHomeRoute(AsyncValue<UserSession?> authState) {
  return authState.when(
    data: (user) {
      if (user == null) return '/login';
      switch (user.role) {
        case UserRole.shopper:
          return '/shopper';
        case UserRole.brand:
          return '/brand';
        case UserRole.admin:
          return '/admin-redirect';
      }
    },
    loading: () => '/login',
    error: (_, __) => '/login',
  );
}
