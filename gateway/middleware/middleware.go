// middleware/middleware.go
//
// LESSON: Go middleware
//
// Middleware is a function that wraps an HTTP handler.
// It runs BEFORE and/or AFTER your actual handler logic.
// Common uses: logging, auth checks, request IDs, rate limiting.
//
// Go middleware signature:
//   func(next http.Handler) http.Handler
//
// "next" is the handler this middleware wraps.
// Calling next.ServeHTTP(w, r) passes control to the next layer.

package middleware

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"time"

	"github.com/google/uuid"
)

// ── Context keys ──────────────────────────────────────────────
// LESSON: typed context keys
// Go's context.Context stores key-value pairs.
// Using a custom type (not a plain string) prevents key collisions
// between packages — two packages can't accidentally share "requestID".

type contextKey string

const RequestIDKey contextKey = "requestID"

// ── 1. Request ID middleware ──────────────────────────────────
// Tags every request with a unique ID.
// This ID appears in logs and response headers — critical for
// tracing a single request across multiple services.

func RequestID(next http.Handler) http.Handler {
	// http.HandlerFunc converts a plain function into an http.Handler
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestID := uuid.New().String()

		// Store in context so handlers can access it
		ctx := context.WithValue(r.Context(), RequestIDKey, requestID)

		// Add to response headers so Flutter can correlate requests
		w.Header().Set("X-Request-ID", requestID)

		// Pass the updated request (with new context) down the chain
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// ── 2. Logger middleware ──────────────────────────────────────
// Logs every request: method, path, duration, status code.
// We wrap the ResponseWriter to capture the status code after the
// handler runs — the standard ResponseWriter doesn't expose it.

type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func newResponseWriter(w http.ResponseWriter) *responseWriter {
	return &responseWriter{w, http.StatusOK} // default 200
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

func Logger(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		wrapped := newResponseWriter(w)

		next.ServeHTTP(wrapped, r) // run the actual handler

		// Log AFTER the handler returns so we have the status code + duration
		requestID, _ := r.Context().Value(RequestIDKey).(string)
		log.Printf(
			"[%s] %s %s → %d (%s)",
			requestID[:8], // first 8 chars of UUID is enough
			r.Method,
			r.URL.Path,
			wrapped.statusCode,
			time.Since(start),
		)
	})
}

// ── 3. JSON helper ────────────────────────────────────────────
// Go doesn't have FastAPI's automatic JSON serialization.
// We write this helper once so every handler can call:
//   WriteJSON(w, 200, myData)
// instead of repeating json.Marshal + headers every time.

func WriteJSON(w http.ResponseWriter, status int, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		log.Printf("WriteJSON error: %v", err)
	}
}

func WriteError(w http.ResponseWriter, status int, message string) {
	WriteJSON(w, status, map[string]string{"error": message})
}
