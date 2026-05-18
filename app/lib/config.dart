// lib/config.dart
//
// LESSON: Flutter environment config
// We use --dart-define at build time to inject the API URL.
// Local dev uses localhost, production uses the Railway URL.
// This way the same code works in both environments.

class AppConfig {
  // Injected at build time via --dart-define=API_URL=https://...
  // Falls back to localhost for local development
  static const String apiUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://localhost:8000',
  );

  static const String wsUrl = String.fromEnvironment(
    'WS_URL',
    defaultValue: 'ws://localhost:8000',
  );
}
