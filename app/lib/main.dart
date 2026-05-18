// lib/main.dart
//
// LESSON: Flutter app structure
//
// Every Flutter app starts from main() → runApp().
// runApp() takes a Widget — the root of your entire UI tree.
//
// MaterialApp sets up:
//   - Navigation (routes, navigator)
//   - Theme (colors, fonts, dark/light mode)
//   - Localisation (language/region)
//
// ChangeNotifierProvider wraps the whole app so ANY widget
// can access DebateProvider via context.watch/read.

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'models/debate_provider.dart';
import 'screens/setup_screen.dart';

void main() {
  runApp(const LioMalauApp());
}

class LioMalauApp extends StatelessWidget {
  const LioMalauApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      // create: builds the provider once when the app starts
      create: (_) => DebateProvider(),
      child: MaterialApp(
        title: 'lioMalau',
        debugShowCheckedModeBanner: false,

        // Dark theme — fits the serious nature of the app
        theme: ThemeData(
          brightness: Brightness.dark,
          colorScheme: const ColorScheme.dark(
            primary: Colors.amber,
            secondary: Colors.amber,
            surface: Color(0xFF111111),
          ),
          scaffoldBackgroundColor: Colors.black,
          appBarTheme: const AppBarTheme(
            backgroundColor: Color(0xFF0A0A0A),
            elevation: 0,
          ),
          fontFamily: 'SF Pro Display', // falls back to system font
        ),

        home: const SetupScreen(),
      ),
    );
  }
}
