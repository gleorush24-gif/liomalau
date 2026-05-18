# ── Stage 1: Build ───────────────────────────────────────────
# LESSON: multi-stage Docker builds
# We use TWO FROM statements. Stage 1 compiles the Go binary.
# Stage 2 copies only the binary into a tiny image.
# Result: the final image is ~10MB instead of ~800MB.
# The compiler, source code, and build tools never ship to production.

FROM golang:1.22-alpine AS builder

WORKDIR /build

# Copy go.mod first — Docker caches this layer.
# If only .go files changed (not dependencies), the slow
# `go mod download` step is skipped entirely.
COPY go.mod go.sum ./
RUN go mod download

COPY . .

# CGO_ENABLED=0 = pure Go binary (no C dependencies)
# -ldflags="-w -s" = strip debug symbols (smaller binary)
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o gateway ./cmd/main.go


# ── Stage 2: Run ─────────────────────────────────────────────
FROM alpine:3.19

# ca-certificates needed for HTTPS calls to the AI engine
RUN apk --no-cache add ca-certificates

WORKDIR /app
COPY --from=builder /build/gateway .

EXPOSE 8000

CMD ["./gateway"]
