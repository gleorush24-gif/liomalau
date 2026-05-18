// lib/screens/paste_exchange_screen.dart

import 'dart:convert';
import '../config.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:http/http.dart' as http;
import '../models/debate_provider.dart';
import '../models/models.dart';
import '../widgets/verdict_card.dart';
import '../widgets/score_panel.dart';

class PasteExchangeScreen extends StatefulWidget {
  const PasteExchangeScreen({super.key});

  @override
  State<PasteExchangeScreen> createState() => _PasteExchangeScreenState();
}

class _PasteExchangeScreenState extends State<PasteExchangeScreen> {
  final _pasteController = TextEditingController();
  final _scrollController = ScrollController();

  // State machine: idle -> parsing -> preview -> running -> done
  String _phase = 'idle';
  List<_ParsedTurn> _parsedTurns = [];
  List<String> _detectedSpeakers = [];
  List<DebateTurn> _completedTurns = [];
  List<PartyScore> _scores = [];
  String? _error;
  int _currentlyRunning = 0;

  @override
  void dispose() {
    _pasteController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  // ── Step 1: Parse the pasted exchange ────────────────────────
  Future<void> _parseExchange() async {
    final provider = context.read<DebateProvider>();
    final session = provider.session;
    if (session == null) return;

    setState(() {
      _phase = 'parsing';
      _error = null;
    });

    try {
      final response = await http.post(
        Uri.parse('${AppConfig.apiUrl}/api/v1/exchange/parse'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'raw_exchange': _pasteController.text.trim(),
          'session_id': session.sessionId,
          'party_a_id': session.parties[0].id,
          'party_b_id': session.parties[1].id,
          'party_a_label': session.parties[0].label,
          'party_b_label': session.parties[1].label,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _parsedTurns = (data['turns'] as List)
              .map((t) => _ParsedTurn.fromJson(t, session))
              .toList();
          _detectedSpeakers = List<String>.from(data['detected_speakers'] ?? []);
          _phase = 'preview';
        });
      } else {
        final error = jsonDecode(response.body);
        setState(() {
          _error = error['detail'] ?? 'Failed to parse exchange';
          _phase = 'idle';
        });
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _phase = 'idle';
      });
    }
  }

  // ── Step 2: Run all turns through the judge ──────────────────
  Future<void> _runExchange() async {
    final provider = context.read<DebateProvider>();
    final session = provider.session;
    if (session == null) return;

    setState(() {
      _phase = 'running';
      _completedTurns = [];
      _scores = List.from(session.parties);
    });

    try {
      final response = await http.post(
        Uri.parse('${AppConfig.apiUrl}/api/v1/exchange/run'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'session_id': session.sessionId,
          'party_a_id': session.parties[0].id,
          'party_b_id': session.parties[1].id,
          'turns': _parsedTurns.map((t) => t.toJson()).toList(),
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final verdicts = (data['verdicts'] as List)
            .map((v) => VerdictResponse.fromJson(v))
            .toList();

        // Build completed turns with verdicts
        List<DebateTurn> turns = [];
        for (int i = 0; i < _parsedTurns.length && i < verdicts.length; i++) {
          final t = _parsedTurns[i];
          turns.add(DebateTurn(
            partyId: t.partyId,
            partyLabel: t.speakerLabel,
            rawText: t.text,
            verdict: verdicts[i],
            isLoading: false,
          ));

          // Update scores
          final partyIdx = _scores.indexWhere((s) => s.id == t.partyId);
          if (partyIdx != -1) {
            final cur = _scores[partyIdx];
            _scores[partyIdx] = PartyScore(
              id: cur.id,
              label: cur.label,
              score: cur.score + verdicts[i].scoreDelta,
            );
          }

          setState(() {
            _completedTurns = List.from(turns);
            _currentlyRunning = i + 1;
          });

          // Small delay so user sees cards appearing one by one
          await Future.delayed(const Duration(milliseconds: 300));
          _scrollToBottom();
        }

        setState(() => _phase = 'done');
      } else {
        final error = jsonDecode(response.body);
        setState(() {
          _error = error['detail'] ?? 'Failed to run exchange';
          _phase = 'preview';
        });
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _phase = 'preview';
      });
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 400),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _reset() {
    setState(() {
      _phase = 'idle';
      _parsedTurns = [];
      _completedTurns = [];
      _scores = [];
      _error = null;
      _pasteController.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<DebateProvider>();
    final session = provider.session;

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.grey[950],
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('lioMalau',
                style: TextStyle(color: Colors.amber, fontSize: 16, fontWeight: FontWeight.bold)),
            Text('Import Social Exchange',
                style: TextStyle(color: Colors.grey, fontSize: 12)),
          ],
        ),
        actions: [
          if (_phase != 'idle')
            IconButton(
              icon: const Icon(Icons.refresh, color: Colors.grey),
              onPressed: _reset,
              tooltip: 'Start over',
            ),
        ],
      ),
      body: _buildBody(session),
    );
  }

  Widget _buildBody(session) {
    switch (_phase) {
      case 'idle':
        return _PasteInput(
          controller: _pasteController,
          onParse: _parseExchange,
          error: _error,
        );

      case 'parsing':
        return const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(color: Colors.amber),
              SizedBox(height: 20),
              Text('Reading the exchange...', style: TextStyle(color: Colors.grey)),
              SizedBox(height: 8),
              Text('Identifying speakers and arguments',
                  style: TextStyle(color: Colors.grey, fontSize: 12)),
            ],
          ),
        );

      case 'preview':
        return _PreviewTurns(
          turns: _parsedTurns,
          speakers: _detectedSpeakers,
          error: _error,
          onRun: _runExchange,
          onReset: _reset,
        );

      case 'running':
      case 'done':
        return _ResultsView(
          turns: _completedTurns,
          scores: _scores,
          totalTurns: _parsedTurns.length,
          currentlyRunning: _currentlyRunning,
          isRunning: _phase == 'running',
          scrollController: _scrollController,
          session: session,
        );

      default:
        return const SizedBox();
    }
  }
}

// ── Paste input screen ────────────────────────────────────────
class _PasteInput extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onParse;
  final String? error;

  const _PasteInput({
    required this.controller,
    required this.onParse,
    this.error,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Paste a social media exchange',
            style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          Text(
            'Twitter/X threads, Facebook arguments, Reddit debates, WhatsApp chats — paste the raw text and the judge will analyse each argument.',
            style: TextStyle(color: Colors.grey[500], fontSize: 13, height: 1.4),
          ),
          const SizedBox(height: 16),

          // Paste area
          Expanded(
            child: TextField(
              controller: controller,
              maxLines: null,
              expands: true,
              textAlignVertical: TextAlignVertical.top,
              style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.5),
              decoration: InputDecoration(
                hintText:
                    'Paste exchange here...\n\nExample:\n@UserA: Israel has every right to defend itself\n@UserB: The bombing of civilian infrastructure violates Geneva Convention\n@UserA: Hamas started it by launching rockets\n@UserB: That does not justify collective punishment under Article 33...',
                hintStyle: TextStyle(color: Colors.grey[700], fontSize: 12),
                filled: true,
                fillColor: Colors.grey[900],
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: BorderSide(color: Colors.grey[700]!),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: BorderSide(color: Colors.grey[700]!),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: const BorderSide(color: Colors.amber),
                ),
              ),
            ),
          ),

          const SizedBox(height: 12),

          if (error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Text(error!, style: const TextStyle(color: Colors.red, fontSize: 12)),
            ),

          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton.icon(
              onPressed: onParse,
              icon: const Icon(Icons.auto_fix_high, color: Colors.black),
              label: const Text('Extract Arguments',
                  style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.amber,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Preview parsed turns ──────────────────────────────────────
class _PreviewTurns extends StatelessWidget {
  final List<_ParsedTurn> turns;
  final List<String> speakers;
  final String? error;
  final VoidCallback onRun;
  final VoidCallback onReset;

  const _PreviewTurns({
    required this.turns,
    required this.speakers,
    this.error,
    required this.onRun,
    required this.onReset,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Summary header
        Container(
          padding: const EdgeInsets.all(14),
          color: Colors.grey[900],
          child: Row(
            children: [
              const Icon(Icons.check_circle, color: Colors.green, size: 18),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  '${turns.length} arguments extracted from ${speakers.length} speakers',
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
        ),

        // Detected speakers
        if (speakers.isNotEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            child: Row(
              children: [
                Text('Speakers: ', style: TextStyle(color: Colors.grey[500], fontSize: 12)),
                ...speakers.asMap().entries.map((e) => Container(
                      margin: const EdgeInsets.only(right: 6),
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: e.key == 0 ? Colors.blue[900] : Colors.purple[900],
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(e.value,
                          style: const TextStyle(color: Colors.white, fontSize: 11)),
                    )),
              ],
            ),
          ),

        // Turns list
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            itemCount: turns.length,
            itemBuilder: (context, i) {
              final t = turns[i];
              final isA = t.side == 'A';
              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: isA ? Colors.blue[900]!.withOpacity(0.2) : Colors.purple[900]!.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(8),
                  border: Border(
                    left: BorderSide(
                      color: isA ? Colors.blue[400]! : Colors.purple[400]!,
                      width: 3,
                    ),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(children: [
                      Text(
                        '${i + 1}. ${t.speakerLabel}',
                        style: TextStyle(
                          color: isA ? Colors.blue[300] : Colors.purple[300],
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const Spacer(),
                      Text('Party ${t.side}',
                          style: TextStyle(color: Colors.grey[500], fontSize: 10)),
                    ]),
                    const SizedBox(height: 4),
                    Text(t.text,
                        style: TextStyle(color: Colors.grey[300], fontSize: 12, height: 1.4)),
                  ],
                ),
              );
            },
          ),
        ),

        // Action buttons
        Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            children: [
              if (error != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Text(error!, style: const TextStyle(color: Colors.red, fontSize: 12)),
                ),
              Row(children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: onReset,
                    style: OutlinedButton.styleFrom(
                      side: BorderSide(color: Colors.grey[600]!),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    child: const Text('Re-paste', style: TextStyle(color: Colors.grey)),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  flex: 2,
                  child: ElevatedButton.icon(
                    onPressed: onRun,
                    icon: const Icon(Icons.gavel, color: Colors.black, size: 18),
                    label: Text(
                      'Judge ${turns.length} Arguments',
                      style: const TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.amber,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                  ),
                ),
              ]),
            ],
          ),
        ),
      ],
    );
  }
}

// ── Results view ──────────────────────────────────────────────
class _ResultsView extends StatelessWidget {
  final List<DebateTurn> turns;
  final List<PartyScore> scores;
  final int totalTurns;
  final int currentlyRunning;
  final bool isRunning;
  final ScrollController scrollController;
  final dynamic session;

  const _ResultsView({
    required this.turns,
    required this.scores,
    required this.totalTurns,
    required this.currentlyRunning,
    required this.isRunning,
    required this.scrollController,
    required this.session,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Progress + score panel
        Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            children: [
              if (isRunning)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    children: [
                      const SizedBox(
                        width: 14,
                        height: 14,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.amber),
                      ),
                      const SizedBox(width: 10),
                      Text(
                        'Judging argument $currentlyRunning of $totalTurns...',
                        style: TextStyle(color: Colors.amber, fontSize: 12),
                      ),
                    ],
                  ),
                ),
              ScorePanel(scores: scores),
            ],
          ),
        ),

        // Verdict cards
        Expanded(
          child: ListView.builder(
            controller: scrollController,
            itemCount: turns.length,
            itemBuilder: (context, i) {
              final turn = turns[i];
              final isLeft = session != null
                  ? turn.partyId == session.parties[0].id
                  : i % 2 == 0;
              return VerdictCard(turn: turn, isLeft: isLeft);
            },
          ),
        ),
      ],
    );
  }
}

// ── Data model for parsed turn ────────────────────────────────
class _ParsedTurn {
  final String speakerLabel;
  final String partyId;
  final String text;
  final int turnOrder;
  final String side;

  _ParsedTurn({
    required this.speakerLabel,
    required this.partyId,
    required this.text,
    required this.turnOrder,
    required this.side,
  });

  factory _ParsedTurn.fromJson(Map<String, dynamic> json, dynamic session) {
    final side = json['side'] as String? ?? 'A';
    return _ParsedTurn(
      speakerLabel: json['speaker_label'] as String,
      partyId: json['party_id'] as String,
      text: json['text'] as String,
      turnOrder: json['turn_order'] as int,
      side: side,
    );
  }

  Map<String, dynamic> toJson() => {
        'speaker_label': speakerLabel,
        'party_id': partyId,
        'text': text,
        'turn_order': turnOrder,
        'side': side,
      };
}
