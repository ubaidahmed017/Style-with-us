import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';

class ApiClient {
  static const String baseUrl = 'http://localhost:8000';
  late Dio _dio;

  ApiClient() {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
    ));

    // Add auth interceptor
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final user = FirebaseAuth.instance.currentUser;
          if (user != null) {
            final token = await user.getIdToken();
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onError: (error, handler) async {
          if (error.response?.statusCode == 401) {
            // Token expired, refresh and retry
            try {
              final user = FirebaseAuth.instance.currentUser;
              if (user != null) {
                final newToken = await user.getIdToken(true);

                final options = error.requestOptions;
                options.headers['Authorization'] = 'Bearer $newToken';

                final response = await _dio.request(
                  options.path,
                  options: Options(
                    method: options.method,
                    headers: options.headers,
                  ),
                  data: options.data,
                  queryParameters: options.queryParameters,
                );
                return handler.resolve(response);
              }
            } catch (e) {
              return handler.next(error);
            }
          }
          return handler.next(error);
        },
      ),
    );
  }

  Dio get dio => _dio;

  // User endpoints
  Future<Response> registerUser(String name, String email, String role) {
    return _dio.post('/users/register', data: {
      'name': name,
      'email': email,
      'role': role,
    });
  }

  Future<Response> updateUserProfile(Map<String, dynamic> profile) {
    return _dio.post('/users/profile', data: profile);
  }

  Future<Response> getUserProfile() {
    return _dio.get('/users/profile');
  }

  // Product endpoints
  Future<Response> getProducts({
    int page = 1,
    int pageSize = 20,
    String? gender,
    String? sizeLabel,
    String? brandId,
  }) {
    return _dio.get('/inventory/products', queryParameters: {
      'page': page,
      'page_size': pageSize,
      if (gender != null) 'gender': gender,
      if (sizeLabel != null) 'size_label': sizeLabel,
      if (brandId != null) 'brand_id': brandId,
    });
  }

  Future<Response> getRecommendations() {
    return _dio.get('/recommendations/outfits');
  }

  // Payment endpoints
  Future<Response> createPaymentIntent(List<Map<String, dynamic>> items) {
    return _dio.post('/payments/create-intent', data: {'items': items});
  }

  // ML endpoints
  Future<Response> submitStyleAnalysis(String imageUrl) {
    return _dio.post('/ml/style-analysis', data: {'image_url': imageUrl});
  }

  Future<Response> getJobStatus(String jobId) {
    return _dio.get('/ml/jobs/$jobId');
  }
}
