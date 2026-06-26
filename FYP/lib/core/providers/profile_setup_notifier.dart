import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api_client.dart';

enum UnitPreference { metric, imperial }

class UserProfile {
  final String? gender; // male, female, non_binary
  final UnitPreference unitPreference;
  final double? height;
  final double? weight;
  final int? age;
  final double? chest;
  final double? waist;
  final double? hips;
  final double? inseam;
  final double? shoulderWidth;

  UserProfile({
    this.gender,
    this.unitPreference = UnitPreference.metric,
    this.height,
    this.weight,
    this.age,
    this.chest,
    this.waist,
    this.hips,
    this.inseam,
    this.shoulderWidth,
  });

  UserProfile copyWith({
    String? gender,
    UnitPreference? unitPreference,
    double? height,
    double? weight,
    int? age,
    double? chest,
    double? waist,
    double? hips,
    double? inseam,
    double? shoulderWidth,
  }) =>
      UserProfile(
        gender: gender ?? this.gender,
        unitPreference: unitPreference ?? this.unitPreference,
        height: height ?? this.height,
        weight: weight ?? this.weight,
        age: age ?? this.age,
        chest: chest ?? this.chest,
        waist: waist ?? this.waist,
        hips: hips ?? this.hips,
        inseam: inseam ?? this.inseam,
        shoulderWidth: shoulderWidth ?? this.shoulderWidth,
      );

  Map<String, dynamic> toJson() => {
    'gender': gender,
    'height_cm': height,
    'weight_kg': weight,
    'age': age,
    'chest_cm': chest,
    'waist_cm': waist,
    'hips_cm': hips,
    'inseam_cm': inseam,
    'shoulder_width_cm': shoulderWidth,
    'unit_preference': unitPreference == UnitPreference.metric ? 'metric' : 'imperial',
  };
}

class ProfileSetupNotifier extends Notifier<UserProfile> {
  late final ApiClient _apiClient;

  @override
  UserProfile build() {
    _apiClient = ApiClient();
    return UserProfile();
  }

  void setGender(String gender) {
    state = state.copyWith(gender: gender);
  }

  void setUnitPreference(UnitPreference unit) {
    state = state.copyWith(unitPreference: unit);
  }

  void setHeight(double? height) {
    state = state.copyWith(height: height);
  }

  void setWeight(double? weight) {
    state = state.copyWith(weight: weight);
  }

  void setAge(int? age) {
    state = state.copyWith(age: age);
  }

  void setChest(double? chest) {
    state = state.copyWith(chest: chest);
  }

  void setWaist(double? waist) {
    state = state.copyWith(waist: waist);
  }

  void setHips(double? hips) {
    state = state.copyWith(hips: hips);
  }

  void setInseam(double? inseam) {
    state = state.copyWith(inseam: inseam);
  }

  void setShoulderWidth(double? shoulderWidth) {
    state = state.copyWith(shoulderWidth: shoulderWidth);
  }

  Future<void> submitProfile() async {
    if (state.gender == null) {
      throw Exception('Gender is required');
    }

    await _apiClient.updateUserProfile(state.toJson());
  }

  void reset() {
    state = UserProfile();
  }
}

final profileSetupProvider =
    NotifierProvider<ProfileSetupNotifier, UserProfile>(() {
  return ProfileSetupNotifier();
});

final isGenderSelectedProvider = Provider<bool>((ref) {
  return ref.watch(profileSetupProvider).gender != null;
});
