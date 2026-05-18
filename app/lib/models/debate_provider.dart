// lib/models/debate_provider.dart
//
// LESSON: Provider + ChangeNotifier (state management)
//
// The Problem: Flutter widgets are functions that return UI.
// When data changes, the UI needs to rebuild.
// But how does a widget deep in the tree know data changed?
//
// Provider solves this:
//   1. DebateProvider extends ChangeNotifier (holds all app state)
//   2. Wrap the app in ChangeNotifierProvider (makes it available everywhere)
//   3. Any widget calls context.watch<DebateProvider>() to subscribe
//   4. When we call notifyListeners(), all subscribed widgets rebuild
//
// This is Flutter's equivalent of React's Context + useState.

import 'package:flutter/foundation.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';

class DebateProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  final WebSocketService _ws = WebSocketService();

  // ── State ─────────────────────────────────────────────────
  SessionResponse? session;
  List<DebateTurn> turns = [];
  List<PartyScore> scores = [];
  bool isCreatingSession = false;
  bool isSubmitting = false;
  String? errorMessage;

  // Which party is currently "active" (submitting)
  int activePartyIndex = 0;

  PartyScore? get activeParty =>
      session != null && scores.isNotEmpty ? scores[activePartyIndex] : null;

  DebateProvider() {
    // Listen to WebSocket streams — update state when messages arrive
    _ws.scoreStream.listen((newScores) {
      scores = newScores;
      notifyListeners(); // triggers UI rebuild in all watching widgets
    });
  }

  // ── Create Session ─────────────────────────────────────────
  Future<void> createSession(String title, String labelA, String labelB) async {
    isCreatingSession = true;
    errorMessage = null;
    notifyListeners();

    try {
      session = await _api.createSession(
        title: title,
        partyLabels: [labelA, labelB],
      );

      // Initialize scores from session data
      scores = session!.parties;

      // Connect WebSocket for live updates
      _ws.connect(session!.sessionId);

      notifyListeners();
    } catch (e) {
      errorMessage = e.toString();
      notifyListeners();
    } finally {
      // LESSON: finally block
      // Runs whether the try succeeded or threw — perfect for cleanup
      // like setting isLoading = false
      isCreatingSession = false;
      notifyListeners();
    }
  }

  // ── Submit Argument ────────────────────────────────────────
  Future<void> submitArgument(String rawText) async {
    if (session == null || activeParty == null) return;

    isSubmitting = true;
    errorMessage = null;

    // Add a loading turn to the feed immediately (optimistic UI)
    final loadingTurn = DebateTurn(
      partyId: activeParty!.id,
      partyLabel: activeParty!.label,
      rawText: rawText,
      isLoading: true,
    );
    turns.add(loadingTurn);
    notifyListeners();

    try {
      final verdict = await _api.submitArgument(
        sessionId: session!.sessionId,
        partyId: activeParty!.id,
        rawText: rawText,
        round: (turns.length / 2).ceil(),
      );

      // Replace loading turn with real verdict
      final index = turns.indexOf(loadingTurn);
      if (index != -1) {
        turns[index] = loadingTurn.copyWith(
          verdict: verdict,
          isLoading: false,
        );
      }

      // Update scores locally (WebSocket will also update them)
      final partyIndex = scores.indexWhere((s) => s.id == activeParty!.id);
      if (partyIndex != -1) {
        final current = scores[partyIndex];
        scores[partyIndex] = PartyScore(
          id: current.id,
          label: current.label,
          score: current.score + verdict.scoreDelta,
        );
      }

      // Switch to the other party for the next turn
      activePartyIndex = activePartyIndex == 0 ? 1 : 0;

      notifyListeners();
    } catch (e) {
      errorMessage = e.toString();
      // Remove the loading turn on error
      turns.remove(loadingTurn);
      notifyListeners();
    } finally {
      isSubmitting = false;
      notifyListeners();
    }
  }

  // ── Reset ──────────────────────────────────────────────────
  void reset() {
    _ws.disconnect();
    session = null;
    turns = [];
    scores = [];
    activePartyIndex = 0;
    errorMessage = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _api.dispose();
    _ws.dispose();
    super.dispose();
  }
}
