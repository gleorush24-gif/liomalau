// cmd/main.go
//
// LESSON: Go program structure
//
// Every Go program starts from package main, func main().
// Unlike Python (top-to-bottom execution), Go is compiled —
// main() is the single entry point the OS calls.
//
// Go imports are explicit — if you import something you don't use,
// the compiler REFUSES to build. No dead imports, ever.

package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	chimw "github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
	"github.com/joho/godotenv"

	"github.com/liomalau/gateway/handlers"
	mw "github.com/liomalau/gateway/middleware"
)

func main() {
	// Load .env file (ignored in production where env vars are injected)
	_ = godotenv.Load()

	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}

	// ── Create the WebSocket hub ──────────────────────────────
	// The hub manages all live Flutter connections.
	// We start it in a goroutine so it runs concurrently.
	hub := handlers.NewHub()
	go hub.Run() // LESSON: `go` keyword starts a goroutine

	// ── Create handlers ───────────────────────────────────────
	h := handlers.NewHandler(hub)

	// ── Set up the router ─────────────────────────────────────
	// LESSON: chi router
	// Chi is a lightweight Go HTTP router. Routes are defined with
	// r.Get(), r.Post() etc. Middleware wraps the entire router
	// or specific route groups.

	r := chi.NewRouter()

	// Global middleware — runs on EVERY request
	r.Use(chimw.Recoverer)  // catches panics so the server doesn't crash
	r.Use(mw.RequestID)     // tags every request with a UUID
	r.Use(mw.Logger)        // logs method, path, status, duration

	// CORS — allow Flutter web/mobile to call this API
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins: []string{"*"}, // lock down in production
		AllowedMethods: []string{"GET", "POST", "OPTIONS"},
		AllowedHeaders: []string{"Accept", "Content-Type", "X-Request-ID"},
	}))

	// ── Routes ───────────────────────────────────────────────
	// LESSON: route grouping
	// r.Route("/api/v1", ...) creates a sub-router.
	// All routes inside are prefixed with /api/v1 automatically.

	r.Get("/health", h.Health)

	r.Route("/api/v1", func(r chi.Router) {
		// Session endpoints
		r.Post("/sessions/", h.CreateSession)
		r.Get("/sessions/{sessionID}/scores", h.GetScores)

		// Argument + verdict endpoint
		r.Post("/arguments/", h.SubmitArgument)

		// Exchange import endpoints
		r.Post("/exchange/parse", h.ParseExchange)
		r.Post("/exchange/run", h.RunExchange)
	})

	// WebSocket endpoint — Flutter connects here for live updates
	// URL: ws://localhost:8000/ws?session_id=<uuid>
	r.Get("/ws", hub.ServeWS)

	// ── Start the server ──────────────────────────────────────
	// LESSON: graceful shutdown
	// We don't just call http.ListenAndServe() because that runs forever
	// and can't be stopped cleanly. Instead:
	// 1. Start server in a goroutine
	// 2. Block on an OS signal channel (Ctrl+C sends SIGINT)
	// 3. When signal arrives, give in-flight requests 10s to finish
	// 4. Then shut down

	srv := &http.Server{
		Addr:         ":" + port,
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 60 * time.Second, // longer for AI engine calls
		IdleTimeout:  120 * time.Second,
	}

	// Start server in background goroutine
	go func() {
		log.Printf("🚀 Gateway listening on :%s", port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Server error: %v", err)
		}
	}()

	// Block until we receive SIGINT (Ctrl+C) or SIGTERM (Docker stop)
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit // this line BLOCKS until a signal arrives

	log.Println("Shutting down gateway...")

	// Give in-flight requests 10 seconds to complete
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatalf("Forced shutdown: %v", err)
	}

	log.Println("Gateway stopped cleanly")
}
