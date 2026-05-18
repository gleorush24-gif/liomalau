// lib/models/models.dart
//
// LESSON: Dart classes + fromJson
//
// Dart is strongly typed like Go, but with a more familiar OOP syntax.
// `fromJson` is a named constructor — a factory that builds an object
// from a Map (which is what JSON decodes to in Dart).
// `toJson` converts back to a Map for sending to the API.
//
// Key Dart syntax differences from Python/Go:
//   final = assigned once, can't be reassigned (like Go's const for variables)
//   ? after type = nullable (String? means "String or null")
//   required = named parameter that must be provided
//   => single-expression function shorthand

class PrecedentMatch {
  final String id;
  final String sourceCode;
  final String articleRef;
  final String summary;
  final String stance;
  final double weight;
  final double similarity;

  const PrecedentMatch({
    required this.id,
    required this.sourceCode,
    required this.articleRef,
    required this.summary,
    required this.stance,
    required this.weight,
    required this.similarity,
  });

  // Named constructor — builds from JSON map
  factory PrecedentMatch.fromJson(Map<String, dynamic> json) => PrecedentMatch(
        id: json['id'],
        sourceCode: json['source_code'],
        articleRef: json['article_ref'] ?? '',
        summary: json['summary'],
        stance: json['stance'],
        weight: (json['weight'] as num).toDouble(),
        similarity: (json['similarity'] as num).toDouble(),
      );
}

class VerdictResponse {
  final String argumentId;
  final String parsedClaim;
  final List<PrecedentMatch> precedents;
  final String counterArgument;
  final double scoreDelta;
  final String overallStance;
  final double confidence;
  final String explanation;
  final DateTime createdAt;

  const VerdictResponse({
    required this.argumentId,
    required this.parsedClaim,
    required this.precedents,
    required this.counterArgument,
    required this.scoreDelta,
    required this.overallStance,
    required this.confidence,
    required this.explanation,
    required this.createdAt,
  });

  factory VerdictResponse.fromJson(Map<String, dynamic> json) => VerdictResponse(
        argumentId: json['argument_id'],
        parsedClaim: json['parsed_claim'],
        precedents: (json['precedents'] as List)
            .map((p) => PrecedentMatch.fromJson(p))
            .toList(),
        counterArgument: json['counter_argument'],
        scoreDelta: (json['score_delta'] as num).toDouble(),
        overallStance: json['overall_stance'],
        confidence: (json['confidence'] as num).toDouble(),
        explanation: json['explanation'],
        createdAt: DateTime.parse(json['created_at']),
      );
}

class PartyScore {
  final String id;
  final String label;
  final double score;

  const PartyScore({
    required this.id,
    required this.label,
    required this.score,
  });

  factory PartyScore.fromJson(Map<String, dynamic> json) => PartyScore(
        id: json['id'],
        label: json['label'],
        score: (json['score'] as num).toDouble(),
      );
}

class SessionResponse {
  final String sessionId;
  final String title;
  final List<PartyScore> parties;
  final String status;

  const SessionResponse({
    required this.sessionId,
    required this.title,
    required this.parties,
    required this.status,
  });

  factory SessionResponse.fromJson(Map<String, dynamic> json) => SessionResponse(
        sessionId: json['session_id'],
        title: json['title'],
        parties: (json['parties'] as List)
            .map((p) => PartyScore.fromJson(p))
            .toList(),
        status: json['status'],
      );
}

// A debate "turn" — one argument + its verdict shown in the exchange feed
class DebateTurn {
  final String partyId;
  final String partyLabel;
  final String rawText;
  final VerdictResponse? verdict; // null while loading
  final bool isLoading;

  const DebateTurn({
    required this.partyId,
    required this.partyLabel,
    required this.rawText,
    this.verdict,
    this.isLoading = false,
  });

  DebateTurn copyWith({VerdictResponse? verdict, bool? isLoading}) => DebateTurn(
        partyId: partyId,
        partyLabel: partyLabel,
        rawText: rawText,
        verdict: verdict ?? this.verdict,
        isLoading: isLoading ?? this.isLoading,
      );
}
