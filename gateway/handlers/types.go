// handlers/types.go
//
// LESSON: Go structs and JSON tags
//
// In Go, data shapes are defined as "structs" — like Python dataclasses
// but checked at compile time. The `json:"..."` tags tell Go's JSON
// library what field names to use when encoding/decoding JSON.
//
// Notice there's no "class", no "self", no inheritance.
// Go uses composition: you build complex types by embedding simple ones.

package handlers

import "time"

// ── Inbound from Flutter ──────────────────────────────────────

type ArgumentRequest struct {
	SessionID string `json:"session_id"`
	PartyID   string `json:"party_id"`
	RawText   string `json:"raw_text"`
	Round     int    `json:"round"`
}

type SessionCreateRequest struct {
	Title        string   `json:"title"`
	PartyLabels  []string `json:"party_labels"`
}

// ── Outbound to Flutter ───────────────────────────────────────

type PrecedentMatch struct {
	ID         string  `json:"id"`
	SourceCode string  `json:"source_code"`
	ArticleRef string  `json:"article_ref"`
	Summary    string  `json:"summary"`
	Stance     string  `json:"stance"`
	Weight     float64 `json:"weight"`
	Similarity float64 `json:"similarity"`
}

type VerdictResponse struct {
	ArgumentID      string           `json:"argument_id"`
	ParsedClaim     string           `json:"parsed_claim"`
	Precedents      []PrecedentMatch `json:"precedents"`
	CounterArgument string           `json:"counter_argument"`
	ScoreDelta      float64          `json:"score_delta"`
	OverallStance   string           `json:"overall_stance"`
	Confidence      float64          `json:"confidence"`
	Explanation     string           `json:"explanation"`
	CreatedAt       time.Time        `json:"created_at"`
}

type PartyScore struct {
	ID    string  `json:"id"`
	Label string  `json:"label"`
	Score float64 `json:"score"`
}

type SessionResponse struct {
	SessionID string       `json:"session_id"`
	Title     string       `json:"title"`
	Parties   []PartyScore `json:"parties"`
	Status    string       `json:"status"`
	CreatedAt time.Time    `json:"created_at"`
}

// ── WebSocket messages ────────────────────────────────────────
// LESSON: Go "iota" for typed constants
// Instead of magic strings like "verdict" or "score_update",
// we define a MessageType so the compiler catches typos.

type WSMessageType string

const (
	WSVerdict     WSMessageType = "verdict"
	WSScoreUpdate WSMessageType = "score_update"
	WSError       WSMessageType = "error"
)

type WSMessage struct {
	Type    WSMessageType `json:"type"`
	Payload interface{}   `json:"payload"` // interface{} = any type (like 'any' in TypeScript)
}

// ── API error response ────────────────────────────────────────

type APIError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}
