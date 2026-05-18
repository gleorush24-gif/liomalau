// lib/services/websocket_service.dart
import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../models/models.dart';
import '../config.dart';

class WebSocketService {
  static String get wsBaseUrl => AppConfig.wsUrl;
  WebSocketChannel? _channel;
  final _verdictController = StreamController<VerdictResponse>.broadcast();
  final _scoreController = StreamController<List<PartyScore>>.broadcast();
  Stream<VerdictResponse> get verdictStream => _verdictController.stream;
  Stream<List<PartyScore>> get scoreStream => _scoreController.stream;
  bool get isConnected => _channel != null;

  void connect(String sessionId) {
    disconnect();
    final uri = Uri.parse('$wsBaseUrl/ws?session_id=$sessionId');
    _channel = WebSocketChannel.connect(uri);
    _channel!.stream.listen(
      (data) => _handleMessage(data as String),
      onError: (error) => print('WebSocket error: $error'),
      onDone: () => print('WebSocket disconnected'),
    );
  }

  void _handleMessage(String data) {
    final json = jsonDecode(data) as Map<String, dynamic>;
    final type = json['type'] as String;
    final payload = json['payload'];
    if (type == 'verdict') {
      _verdictController.add(VerdictResponse.fromJson(payload));
    } else if (type == 'score_update') {
      _scoreController.add((payload as List).map((s) => PartyScore.fromJson(s)).toList());
    }
  }

  void disconnect() {
    _channel?.sink.close();
    _channel = null;
  }

  void dispose() {
    disconnect();
    _verdictController.close();
    _scoreController.close();
  }
}
