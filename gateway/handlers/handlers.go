// handlers/handlers.go
//
// LESSON: Go HTTP handlers + proxying
//
// The gateway sits between Flutter and the Python AI engine.
// Flutter only knows about port 8000 (gateway).
// The gateway forwards requests to port 8001 (AI engine).
//
// Why not call the AI engine directly from Flutter?
// 1. Security: the AI engine is never exposed to the public internet
// 2. The gateway adds auth, rate limiting, request IDs
// 3. The gateway handles WebSocket broadcasting after each verdict

package handlers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"

	mw "github.com/liomalau/gateway/middleware"
)

// Handler holds shared dependencies — injected at startup
type Handler struct {
	Hub        *Hub
	HTTPClient *http.Client
	AIBaseURL  string
}

func NewHandler(hub *Hub) *Handler {
	aiURL := os.Getenv("AI_ENGINE_URL")
	if aiURL == "" {
		aiURL = "http://ai-engine:8001"
	}

	return &Handler{
		Hub: hub,
		// Custom HTTP client with timeout — NEVER use http.DefaultClient
		// in production (it has no timeout and can hang forever)
		HTTPClient: &http.Client{Timeout: 30 * time.Second},
		AIBaseURL:  aiURL,
	}
}

// ── POST /api/v1/sessions/ ────────────────────────────────────
func (h *Handler) CreateSession(w http.ResponseWriter, r *http.Request) {
	// LESSON: reading + forwarding request body
	// We read the body, validate it exists, then forward it to the AI engine.
	// We must read it here because http.Request.Body is a stream — it can
	// only be read once. After we read it we create a new reader for forwarding.

	body, err := io.ReadAll(r.Body)
	if err != nil {
		mw.WriteError(w, http.StatusBadRequest, "failed to read request body")
		return
	}

	// Validate it's real JSON before forwarding
	var req SessionCreateRequest
	if err := json.Unmarshal(body, &req); err != nil {
		mw.WriteError(w, http.StatusBadRequest, "invalid JSON: "+err.Error())
		return
	}

	// Forward to AI engine
	resp, err := h.HTTPClient.Post(
		h.AIBaseURL+"/api/v1/sessions/",
		"application/json",
		bytes.NewReader(body), // bytes.NewReader lets us "re-read" the body
	)
	if err != nil {
		log.Printf("AI engine error: %v", err)
		mw.WriteError(w, http.StatusBadGateway, "AI engine unavailable")
		return
	}
	defer resp.Body.Close()

	// Forward the response back to Flutter
	h.forwardResponse(w, resp)
}

// ── POST /api/v1/arguments/ ───────────────────────────────────
// This is the main endpoint — submit an argument, get a verdict,
// broadcast the verdict to all WebSocket clients in the session.

func (h *Handler) SubmitArgument(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		mw.WriteError(w, http.StatusBadRequest, "failed to read request body")
		return
	}

	// Parse to get the session_id for WebSocket broadcasting
	var req ArgumentRequest
	if err := json.Unmarshal(body, &req); err != nil {
		mw.WriteError(w, http.StatusBadRequest, "invalid JSON: "+err.Error())
		return
	}

	if req.SessionID == "" || req.PartyID == "" || req.RawText == "" {
		mw.WriteError(w, http.StatusBadRequest, "session_id, party_id and raw_text are required")
		return
	}

	// Forward to AI engine (this takes 3-5 seconds while GPT-4o rules)
	resp, err := h.HTTPClient.Post(
		h.AIBaseURL+"/api/v1/arguments/",
		"application/json",
		bytes.NewReader(body),
	)
	if err != nil {
		log.Printf("AI engine error: %v", err)
		mw.WriteError(w, http.StatusBadGateway, "AI engine unavailable")
		return
	}
	defer resp.Body.Close()

	// Read response body — we need it for BOTH the HTTP response AND WebSocket
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		mw.WriteError(w, http.StatusInternalServerError, "failed to read AI response")
		return
	}

	// Send HTTP response to the caller (whoever POSTed the argument)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(resp.StatusCode)
	w.Write(respBody)

	// If verdict was successful, broadcast to ALL WebSocket clients
	// watching this session — this is how the live debate feed updates
	if resp.StatusCode == http.StatusCreated {
		var verdict VerdictResponse
		if err := json.Unmarshal(respBody, &verdict); err == nil {
			// Broadcast verdict to all Flutter clients in this session
			h.Hub.Broadcast(req.SessionID, WSVerdict, verdict)

			// Also broadcast updated scores
			go h.broadcastScores(req.SessionID)
		}
	}
}

// ── GET /api/v1/sessions/{sessionID}/scores ──────────────────
func (h *Handler) GetScores(w http.ResponseWriter, r *http.Request) {
	// LESSON: URL path parameters in chi router
	// Chi extracts {sessionID} from the URL path.
	// We get it with chi.URLParam(r, "sessionID")
	// (imported in main.go where the router is defined)
	sessionID := r.URL.Query().Get("session_id")
	if sessionID == "" {
		// Try path param (set by chi router in main.go)
		sessionID = r.PathValue("sessionID")
	}

	resp, err := h.HTTPClient.Get(
		fmt.Sprintf("%s/api/v1/sessions/%s/scores", h.AIBaseURL, sessionID),
	)
	if err != nil {
		mw.WriteError(w, http.StatusBadGateway, "AI engine unavailable")
		return
	}
	defer resp.Body.Close()

	h.forwardResponse(w, resp)
}

// ── Health check ──────────────────────────────────────────────
func (h *Handler) Health(w http.ResponseWriter, r *http.Request) {
	mw.WriteJSON(w, http.StatusOK, map[string]string{
		"status":  "ok",
		"service": "liomalau-gateway",
	})
}

// ── Helpers ───────────────────────────────────────────────────

// forwardResponse copies a response from the AI engine to the client
func (h *Handler) forwardResponse(w http.ResponseWriter, resp *http.Response) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(resp.StatusCode)
	io.Copy(w, resp.Body)
}

// broadcastScores fetches current scores and broadcasts to all session clients
func (h *Handler) broadcastScores(sessionID string) {
	resp, err := h.HTTPClient.Get(
		fmt.Sprintf("%s/api/v1/sessions/%s/scores", h.AIBaseURL, sessionID),
	)
	if err != nil {
		return
	}
	defer resp.Body.Close()

	var scores []PartyScore
	if err := json.NewDecoder(resp.Body).Decode(&scores); err != nil {
		return
	}

	h.Hub.Broadcast(sessionID, WSScoreUpdate, scores)
}

// ── POST /api/v1/exchange/parse ───────────────────────────────
func (h *Handler) ParseExchange(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		mw.WriteError(w, http.StatusBadRequest, "failed to read body")
		return
	}
	resp, err := h.HTTPClient.Post(
		h.AIBaseURL+"/api/v1/exchange/parse",
		"application/json",
		bytes.NewReader(body),
	)
	if err != nil {
		mw.WriteError(w, http.StatusBadGateway, "AI engine unavailable")
		return
	}
	defer resp.Body.Close()
	h.forwardResponse(w, resp)
}

// ── POST /api/v1/exchange/run ─────────────────────────────────
func (h *Handler) RunExchange(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		mw.WriteError(w, http.StatusBadRequest, "failed to read body")
		return
	}
	resp, err := h.HTTPClient.Post(
		h.AIBaseURL+"/api/v1/exchange/run",
		"application/json",
		bytes.NewReader(body),
	)
	if err != nil {
		mw.WriteError(w, http.StatusBadGateway, "AI engine unavailable")
		return
	}
	defer resp.Body.Close()
	h.forwardResponse(w, resp)
}
