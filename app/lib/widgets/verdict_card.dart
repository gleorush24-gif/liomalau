// lib/widgets/verdict_card.dart
import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';
import '../models/models.dart';

class VerdictCard extends StatelessWidget {
  final DebateTurn turn;
  final bool isLeft;
  const VerdictCard({super.key, required this.turn, required this.isLeft});

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final cardWidth = (screenWidth - 48) * 0.78;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      child: Align(
        alignment: isLeft ? Alignment.centerLeft : Alignment.centerRight,
        child: SizedBox(
          width: cardWidth,
          child: turn.isLoading ? _LoadingCard() : _ContentCard(turn: turn, isLeft: isLeft),
        ),
      ),
    );
  }
}

class _LoadingCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Shimmer.fromColors(
      baseColor: Colors.grey[800]!,
      highlightColor: Colors.grey[600]!,
      child: Container(
        height: 120,
        decoration: BoxDecoration(color: Colors.grey[800], borderRadius: BorderRadius.circular(12)),
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(height: 12, width: 200, color: Colors.grey[700]),
          const SizedBox(height: 8),
          Container(height: 10, width: 150, color: Colors.grey[700]),
          const SizedBox(height: 16),
          const Row(children: [
            SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.amber)),
            SizedBox(width: 8),
            Text('Panel judge is ruling...', style: TextStyle(color: Colors.amber, fontSize: 12)),
          ]),
        ]),
      ),
    );
  }
}

class _ContentCard extends StatefulWidget {
  final DebateTurn turn;
  final bool isLeft;
  const _ContentCard({required this.turn, required this.isLeft});
  @override
  State<_ContentCard> createState() => _ContentCardState();
}

class _ContentCardState extends State<_ContentCard> {
  bool _showCitations = false;
  bool _showCounter = false;

  Color get _stanceColor {
    final s = widget.turn.verdict?.overallStance ?? '';
    if (s == 'supports') return Colors.green[400]!;
    if (s == 'contradicts') return Colors.red[400]!;
    return Colors.amber[400]!;
  }

  @override
  Widget build(BuildContext context) {
    final verdict = widget.turn.verdict;
    return Container(
      decoration: BoxDecoration(
        color: Colors.grey[900],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: verdict != null ? _stanceColor.withOpacity(0.4) : Colors.grey[800]!, width: 1.5),
      ),
      padding: const EdgeInsets.all(14),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(child: Text(widget.turn.partyLabel.toUpperCase(), overflow: TextOverflow.ellipsis,
            style: TextStyle(color: Colors.grey[400], fontSize: 10, letterSpacing: 1.2, fontWeight: FontWeight.bold))),
          if (verdict != null) _StanceBadge(stance: verdict.overallStance, delta: verdict.scoreDelta),
        ]),
        const SizedBox(height: 8),
        Text(widget.turn.rawText, style: const TextStyle(color: Colors.white, fontSize: 14)),
        if (verdict != null) ...[
          const SizedBox(height: 10),
          const Divider(color: Colors.grey, height: 1),
          const SizedBox(height: 10),
          Text(verdict.explanation, style: TextStyle(color: Colors.grey[300], fontSize: 12, height: 1.5)),
          const SizedBox(height: 8),
          GestureDetector(
            onTap: () => setState(() => _showCounter = !_showCounter),
            child: Row(children: [
              Icon(_showCounter ? Icons.expand_less : Icons.expand_more, color: Colors.blue[300], size: 16),
              Text(' Counter-argument', style: TextStyle(color: Colors.blue[300], fontSize: 12)),
            ]),
          ),
          if (_showCounter) ...[
            const SizedBox(height: 6),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.blue[900]!.withOpacity(0.3),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.blue[800]!),
              ),
              child: Text(verdict.counterArgument, style: TextStyle(color: Colors.blue[100], fontSize: 12, height: 1.4)),
            ),
          ],
          const SizedBox(height: 6),
          GestureDetector(
            onTap: () => setState(() => _showCitations = !_showCitations),
            child: Row(children: [
              Icon(_showCitations ? Icons.expand_less : Icons.expand_more, color: Colors.amber[300], size: 16),
              Text(' ${verdict.precedents.length} legal citation(s)', style: TextStyle(color: Colors.amber[300], fontSize: 12)),
            ]),
          ),
          if (_showCitations) ...verdict.precedents.map((p) => _CitationRow(precedent: p)),
        ],
      ]),
    );
  }
}

class _StanceBadge extends StatelessWidget {
  final String stance;
  final double delta;
  const _StanceBadge({required this.stance, required this.delta});

  @override
  Widget build(BuildContext context) {
    Color color;
    String label;
    if (stance == 'supports') {
      color = Colors.green[400]!;
      label = '+${delta.toStringAsFixed(0)} SUPPORTED';
    } else if (stance == 'contradicts') {
      color = Colors.red[400]!;
      label = '${delta.toStringAsFixed(0)} CONTRADICTED';
    } else {
      color = Colors.amber[400]!;
      label = 'INCONCLUSIVE';
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Text(label, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold)),
    );
  }
}

class _CitationRow extends StatelessWidget {
  final PrecedentMatch precedent;
  const _CitationRow({required this.precedent});

  @override
  Widget build(BuildContext context) {
    Color sc;
    if (precedent.stance == 'supports') {
      sc = Colors.green[400]!;
    } else if (precedent.stance == 'contradicts') {
      sc = Colors.red[400]!;
    } else {
      sc = Colors.amber[400]!;
    }
    return Container(
      margin: const EdgeInsets.only(top: 6),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.grey[850],
        borderRadius: BorderRadius.circular(6),
        border: Border(left: BorderSide(color: sc, width: 3)),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Flexible(child: Text(precedent.sourceCode, overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: Colors.amber, fontSize: 10, fontWeight: FontWeight.bold))),
          const SizedBox(width: 6),
          Flexible(child: Text(precedent.articleRef, overflow: TextOverflow.ellipsis,
            style: TextStyle(color: Colors.grey[400], fontSize: 10))),
          const Spacer(),
          Text('${(precedent.similarity * 100).toStringAsFixed(0)}% match',
            style: TextStyle(color: Colors.grey[500], fontSize: 9)),
        ]),
        const SizedBox(height: 4),
        Text(precedent.summary, style: TextStyle(color: Colors.grey[300], fontSize: 11)),
      ]),
    );
  }
}
