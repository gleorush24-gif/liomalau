// lib/screens/debate_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/debate_provider.dart';
import '../widgets/score_panel.dart';
import '../widgets/verdict_card.dart';
import 'paste_exchange_screen.dart';

class DebateScreen extends StatefulWidget {
  const DebateScreen({super.key});

  @override
  State<DebateScreen> createState() => _DebateScreenState();
}

class _DebateScreenState extends State<DebateScreen> {
  final _argumentController = TextEditingController();
  final _scrollController = ScrollController();

  @override
  void dispose() {
    _argumentController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  // Scroll to bottom after new turns are added
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

  Future<void> _submit() async {
    final text = _argumentController.text.trim();
    if (text.isEmpty) return;

    _argumentController.clear();

    await context.read<DebateProvider>().submitArgument(text);
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<DebateProvider>();
    final session = provider.session;

    if (session == null) {
      return const Scaffold(
        backgroundColor: Colors.black,
        body: Center(child: CircularProgressIndicator(color: Colors.amber)),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.grey[950],
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'lioMalau',
              style: TextStyle(
                color: Colors.amber,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              session.title,
              style: TextStyle(color: Colors.grey[400], fontSize: 12),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.upload_file, color: Colors.amber),
            tooltip: 'Import social exchange',
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const PasteExchangeScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.grey),
            onPressed: () {
              provider.reset();
              Navigator.of(context).pop();
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Score panel at the top
          Padding(
            padding: const EdgeInsets.all(12),
            child: ScorePanel(
              scores: provider.scores,
              activePartyId: provider.activeParty?.id,
            ),
          ),

          // Debate feed — scrollable list of argument turns
          Expanded(
            child: provider.turns.isEmpty
                ? _EmptyState(partyLabel: provider.activeParty?.label ?? '')
                : ListView.builder(
                    controller: _scrollController,
                    itemCount: provider.turns.length,
                    itemBuilder: (context, index) {
                      final turn = provider.turns[index];
                      // Left side = party A (index 0), right = party B (index 1)
                      final isLeft = turn.partyId == session.parties[0].id;
                      return VerdictCard(turn: turn, isLeft: isLeft);
                    },
                  ),
          ),

          // Error message
          if (provider.errorMessage != null)
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.red[900]!.withOpacity(0.3),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                provider.errorMessage!,
                style: const TextStyle(color: Colors.red, fontSize: 12),
              ),
            ),

          // Input area
          _ArgumentInput(
            controller: _argumentController,
            activeLabel: provider.activeParty?.label ?? '',
            isLoading: provider.isSubmitting,
            onSubmit: _submit,
          ),
        ],
      ),
    );
  }
}

// ── Empty state ───────────────────────────────────────────────
class _EmptyState extends StatelessWidget {
  final String partyLabel;
  const _EmptyState({required this.partyLabel});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text('⚖️', style: TextStyle(fontSize: 48)),
          const SizedBox(height: 16),
          Text(
            'The panel is ready',
            style: TextStyle(color: Colors.grey[400], fontSize: 16),
          ),
          const SizedBox(height: 8),
          Text(
            '$partyLabel submits the first argument',
            style: TextStyle(color: Colors.grey[600], fontSize: 13),
          ),
        ],
      ),
    );
  }
}

// ── Argument input bar ────────────────────────────────────────
class _ArgumentInput extends StatelessWidget {
  final TextEditingController controller;
  final String activeLabel;
  final bool isLoading;
  final VoidCallback onSubmit;

  const _ArgumentInput({
    required this.controller,
    required this.activeLabel,
    required this.isLoading,
    required this.onSubmit,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
      decoration: BoxDecoration(
        color: Colors.grey[950],
        border: Border(top: BorderSide(color: Colors.grey[800]!)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Who is submitting
          Padding(
            padding: const EdgeInsets.only(bottom: 6, left: 4),
            child: Row(
              children: [
                Container(
                  width: 6,
                  height: 6,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.green,
                  ),
                ),
                const SizedBox(width: 6),
                Text(
                  '$activeLabel\'s turn',
                  style: TextStyle(
                    color: Colors.grey[400],
                    fontSize: 11,
                    letterSpacing: 0.5,
                  ),
                ),
              ],
            ),
          ),

          // Input + send button
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: controller,
                  enabled: !isLoading,
                  maxLines: 3,
                  minLines: 1,
                  style: const TextStyle(color: Colors.white, fontSize: 14),
                  decoration: InputDecoration(
                    hintText: 'Submit an argument...',
                    hintStyle: TextStyle(color: Colors.grey[600]),
                    filled: true,
                    fillColor: Colors.grey[900],
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 14, vertical: 10),
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
                  onSubmitted: (_) => onSubmit(),
                ),
              ),
              const SizedBox(width: 10),
              SizedBox(
                width: 48,
                height: 48,
                child: ElevatedButton(
                  onPressed: isLoading ? null : onSubmit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.amber,
                    padding: EdgeInsets.zero,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  child: isLoading
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.black,
                          ),
                        )
                      : const Icon(Icons.send, color: Colors.black, size: 20),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
