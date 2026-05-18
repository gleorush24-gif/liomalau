// lib/services/api_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/models.dart';
import '../config.dart';

class ApiService {
  static String get baseUrl => AppConfig.apiUrl;
  final http.Client _client;
  ApiService() : _client = http.Client();

  Future<SessionResponse> createSession({
    required String title,
    required List<String> partyLabels,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/sessions/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'title': title, 'party_labels': partyLabels}),
    );
    if (response.statusCode == 201) {
      return SessionResponse.fromJson(jsonDecode(response.body));
    }
    throw ApiException(statusCode: response.statusCode, message: 'Failed to create session: ${response.body}');
  }

  Future<VerdictResponse> submitArgument({
    required String sessionId,
    required String partyId,
    required String rawText,
    required int round,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/api/v1/arguments/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'session_id': sessionId, 'party_id': partyId, 'raw_text': rawText, 'round': round}),
    );
    if (response.statusCode == 201) {
      return VerdictResponse.fromJson(jsonDecode(response.body));
    }
    throw ApiException(statusCode: response.statusCode, message: 'Failed to submit argument: ${response.body}');
  }

  Future<List<PartyScore>> getScores(String sessionId) async {
    final response = await _client.get(Uri.parse('$baseUrl/api/v1/sessions/$sessionId/scores'));
    if (response.statusCode == 200) {
      return (jsonDecode(response.body) as List).map((p) => PartyScore.fromJson(p)).toList();
    }
    throw ApiException(statusCode: response.statusCode, message: 'Failed to get scores');
  }

  void dispose() => _client.close();
}

class ApiException implements Exception {
  final int statusCode;
  final String message;
  const ApiException({required this.statusCode, required this.message});
  @override
  String toString() => 'ApiException($statusCode): $message';
}
