import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fyp/core/providers/cart_notifier.dart';
import 'package:fyp/core/providers/profile_setup_notifier.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('CartNotifier Tests', () {
    late ProviderContainer container;

    setUp(() {
      container = ProviderContainer();
    });

    tearDown(() {
      container.dispose();
    });

    test('Initial state is empty', () {
      final cartState = container.read(cartProvider);
      expect(cartState.items, isEmpty);
      expect(cartState.total, 0.0);
    });

    test('Add item to cart', () {
      container.read(cartProvider.notifier).addItem(
        'product-123',
        'Test Product',
        29.99,
        sizeSpecId: 'spec-1',
        sizeLabel: 'M',
      );

      final cartState = container.read(cartProvider);
      expect(cartState.items.length, 1);
      expect(cartState.items.first.productId, 'product-123');
      expect(cartState.items.first.productName, 'Test Product');
      expect(cartState.items.first.price, 29.99);
      expect(cartState.items.first.quantity, 1);
      expect(cartState.total, 29.99);
    });

    test('Increment item quantity in cart', () {
      final notifier = container.read(cartProvider.notifier);
      notifier.addItem(
        'product-123',
        'Test Product',
        29.99,
        sizeSpecId: 'spec-1',
        sizeLabel: 'M',
      );
      notifier.addItem(
        'product-123',
        'Test Product',
        29.99,
        sizeSpecId: 'spec-1',
        sizeLabel: 'M',
      );

      final cartState = container.read(cartProvider);
      expect(cartState.items.length, 1);
      expect(cartState.items.first.quantity, 2);
      expect(cartState.total, 59.98);
    });

    test('Remove item from cart', () {
      final notifier = container.read(cartProvider.notifier);
      notifier.addItem(
        'product-123',
        'Test Product',
        29.99,
        sizeSpecId: 'spec-1',
        sizeLabel: 'M',
      );
      notifier.removeItem('product-123', 'spec-1');

      final cartState = container.read(cartProvider);
      expect(cartState.items, isEmpty);
      expect(cartState.total, 0.0);
    });
  });

  group('ProfileSetupNotifier Tests', () {
    late ProviderContainer container;

    setUp(() {
      container = ProviderContainer();
    });

    tearDown(() {
      container.dispose();
    });

    test('Initial state is empty', () {
      final profile = container.read(profileSetupProvider);
      expect(profile.gender, isNull);
      expect(profile.unitPreference, UnitPreference.metric);
      expect(profile.height, isNull);
    });

    test('Set gender', () {
      container.read(profileSetupProvider.notifier).setGender('male');
      final profile = container.read(profileSetupProvider);
      expect(profile.gender, 'male');
    });

    test('Set unit preference', () {
      container.read(profileSetupProvider.notifier)
          .setUnitPreference(UnitPreference.imperial);
      final profile = container.read(profileSetupProvider);
      expect(profile.unitPreference, UnitPreference.imperial);
    });

    test('Set stats and measurements', () {
      final notifier = container.read(profileSetupProvider.notifier);
      notifier.setHeight(180.0);
      notifier.setWeight(75.0);
      notifier.setAge(25);
      notifier.setChest(96.0);
      notifier.setWaist(78.0);
      notifier.setHips(98.0);

      final profile = container.read(profileSetupProvider);
      expect(profile.height, 180.0);
      expect(profile.weight, 75.0);
      expect(profile.age, 25);
      expect(profile.chest, 96.0);
      expect(profile.waist, 78.0);
      expect(profile.hips, 98.0);
    });
  });
}
