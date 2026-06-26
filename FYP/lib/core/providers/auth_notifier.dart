import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api_client.dart';

enum UserRole { shopper, brand, admin }

class UserSession {
  final String uid;
  final String email;
  final String name;
  final UserRole role;

  UserSession({
    required this.uid,
    required this.email,
    required this.name,
    required this.role,
  });
}

class AuthNotifier extends AsyncNotifier<UserSession?> {
  late final ApiClient _apiClient;
  late final FirebaseAuth _firebaseAuth;
  late final FirebaseFirestore _firestore;

  @override
  Future<UserSession?> build() async {
    _apiClient = ApiClient();
    _firebaseAuth = FirebaseAuth.instance;
    _firestore = FirebaseFirestore.instance;

    // Check if user is already logged in
    final currentUser = _firebaseAuth.currentUser;
    if (currentUser != null) {
      return _getUserSession(currentUser);
    }
    return null;
  }

  Future<void> signUp({
    required String email,
    required String password,
    required String name,
    required String role,
  }) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      // Create Firebase account
      final credential = await _firebaseAuth.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );

      final user = credential.user!;

      // Store user data in Firestore
      await _firestore.collection('users').doc(user.uid).set({
        'uid': user.uid,
        'email': email,
        'name': name,
        'role': role,
        'createdAt': FieldValue.serverTimestamp(),
      });

      // Register with backend
      await _apiClient.registerUser(name, email, role);

      return UserSession(
        uid: user.uid,
        email: email,
        name: name,
        role: _parseRole(role),
      );
    });
  }

  Future<void> signIn({
    required String email,
    required String password,
  }) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final credential = await _firebaseAuth.signInWithEmailAndPassword(
        email: email,
        password: password,
      );

      final user = credential.user!;
      return _getUserSession(user);
    });
  }

  Future<void> signOut() async {
    await _firebaseAuth.signOut();
    state = const AsyncValue.data(null);
  }

  Future<UserSession> _getUserSession(User user) async {
    final doc = await _firestore.collection('users').doc(user.uid).get();
    final data = doc.data() ?? {};

    return UserSession(
      uid: user.uid,
      email: user.email ?? '',
      name: data['name'] ?? '',
      role: _parseRole(data['role'] ?? 'shopper'),
    );
  }

  UserRole _parseRole(String role) {
    switch (role.toLowerCase()) {
      case 'brand':
        return UserRole.brand;
      case 'admin':
        return UserRole.admin;
      default:
        return UserRole.shopper;
    }
  }
}

final authProvider = AsyncNotifierProvider<AuthNotifier, UserSession?>(() {
  return AuthNotifier();
});
