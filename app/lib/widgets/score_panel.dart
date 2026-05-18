// lib/widgets/score_panel.dart

import 'package:flutter/material.dart';
import '../models/models.dart';

class ScorePanel extends StatelessWidget {
  final List<PartyScore> scores;
  final String? activePartyId;

  const ScorePanel({
    super.key,
    required this.scores,
    this.activePartyId,
  });

  @override
  Widget build(BuildContext context) {
    if (scores.isEmpty) return const SizedBox.shrink();

    final total = scores.fold(0.0, (sum, s) => sum + s.score.abs());

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[900],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[800]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'PANEL JUDGE SCOREBOARD',
            style: TextStyle(
              color: Colors.amber,
              fontSize: 11,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.5,
            ),
          ),
          const SizedBox(height: 12),
          ...scores.map((party) => _PartyScoreRow(
                party: party,
                isActive: party.id == activePartyId,
                total: total,
              )),
          const SizedBox(height: 12),
          if (scores.length == 2) _ScoreBar(scores: scores),
        ],
      ),
    );
  }
}

class _PartyScoreRow extends StatelessWidget {
  final PartyScore party;
  final bool isActive;
  final double total;

  const _PartyScoreRow({
    required this.party,
    required this.isActive,
    required this.total,
  });

  @override
  Widget build(BuildContext context) {
    final isPositive = party.score >= 0;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Container(
            width: 8,
            height: 8,
            margin: const EdgeInsets.only(right: 8),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: isActive ? Colors.green : Colors.transparent,
              border: Border.all(
                color: isActive ? Colors.green : Colors.grey[600]!,
              ),
            ),
          ),
          Expanded(
            child: Text(
              party.label,
              overflow: TextOverflow.ellipsis,
              maxLines: 1,
              style: TextStyle(
                color: isActive ? Colors.white : Colors.grey[400],
                fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            '${isPositive ? '+' : ''}${party.score.toStringAsFixed(1)}',
            style: TextStyle(
              color: isPositive ? Colors.green[400] : Colors.red[400],
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
        ],
      ),
    );
  }
}

class _ScoreBar extends StatelessWidget {
  final List<PartyScore> scores;

  const _ScoreBar({required this.scores});

  @override
  Widget build(BuildContext context) {
    final a = scores[0].score;
    final b = scores[1].score;
    final total = a.abs() + b.abs();
    final aFraction = total == 0 ? 0.5 : (a + total) / (total * 2);

    return Column(
      children: [
        const Divider(color: Colors.grey),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: SizedBox(
            height: 8,
            child: Row(
              children: [
                Flexible(
                  flex: (aFraction * 100).round(),
                  child: Container(
                    color: a >= 0 ? Colors.green[600] : Colors.red[600],
                  ),
                ),
                Flexible(
                  flex: ((1 - aFraction) * 100).round(),
                  child: Container(
                    color: b >= 0 ? Colors.green[600] : Colors.red[600],
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 4),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Flexible(
              child: Text(
                scores[0].label,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: Colors.grey[500], fontSize: 10),
              ),
            ),
            const SizedBox(width: 8),
            Flexible(
              child: Text(
                scores[1].label,
                overflow: TextOverflow.ellipsis,
                textAlign: TextAlign.end,
                style: TextStyle(color: Colors.grey[500], fontSize: 10),
              ),
            ),
          ],
        ),
      ],
    );
  }
}