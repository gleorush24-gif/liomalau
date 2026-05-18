// handlers/websocket.go
//
// LESSON: Go goroutines + channels
//
// This is where Go really shines over Python.
// A "goroutine" is a lightweight thread — you can run thousands of them.
// A "channel" is a typed pipe between goroutines — safe communication
// without locks or mutexes.
//
// The Hub pattern:
//   - One central Hub goroutine owns all state (connections map)
//   - Other goroutines send messages TO the hub via channels
//   - The hub is the ONLY one that reads/writes the connections map
//   - This eliminates race conditions entirely — no shared mutable state
//
// Flutter connects here via WebSocket → gets live verdict updates
// without polling the REST API.

package handlers

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"

	"github.com/gorilla/websocket"
)

// ── WebSocket upgrader ────────────────────────────────────────
// Upgrades a plain HTTP connection to WebSocket protocol.
// CheckOrigin: allow all origins in dev (lock down in production).
var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		return true // TODO: restrict to your Flutter app domain in production
	},
}

// ── Client: one connected Flutter instance ───────────────────
type Client struct {
	sessionID string          // which debate session this client is watching
	conn      *websocket.Conn // the WebSocket connection
	send      chan []byte      // buffered channel of outbound messages
}

// ── Hub: central manager of all connections ──────────────────
type Hub struct {
	// LESSON: map in Go
	// map[KeyType]ValueType
	// map[string]map[*Client]bool = sessionID → set of clients
	// We use map[*Client]bool as a "set" (Go has no built-in set type)
	sessions map[string]map[*Client]bool

	broadcast  chan broadcastMsg // incoming messages to send to a session
	register   chan *Client      // new client connections
	unregister chan *Client      // disconnected clients

	// LESSON: sync.Mutex
	// The hub runs in its own goroutine, but register/unregister
	// can come from any goroutine. Mutex protects the sessions map.
	mu sync.RWMutex
}

type broadcastMsg struct {
	sessionID string
	message   []byte
}

// NewHub creates a Hub — call this once at startup
func NewHub() *Hub {
	return &Hub{
		sessions:   make(map[string]map[*Client]bool),
		broadcast:  make(chan broadcastMsg, 256), // buffered: don't block senders
		register:   make(chan *Client),
		unregister: make(chan *Client),
	}
}

// Run starts the hub's event loop — call this in a goroutine: go hub.Run()
func (h *Hub) Run() {
	for {
		// LESSON: select statement
		// Like a switch but for channels. Blocks until ONE channel
		// has data ready, then handles it. This is Go's concurrency primitive.
		select {

		case client := <-h.register:
			h.mu.Lock()
			if h.sessions[client.sessionID] == nil {
				h.sessions[client.sessionID] = make(map[*Client]bool)
			}
			h.sessions[client.sessionID][client] = true
			h.mu.Unlock()
			log.Printf("WS: client joined session %s", client.sessionID)

		case client := <-h.unregister:
			h.mu.Lock()
			if clients, ok := h.sessions[client.sessionID]; ok {
				delete(clients, client)
				close(client.send) // signal the write goroutine to stop
			}
			h.mu.Unlock()
			log.Printf("WS: client left session %s", client.sessionID)

		case msg := <-h.broadcast:
			h.mu.RLock()
			clients := h.sessions[msg.sessionID]
			h.mu.RUnlock()

			for client := range clients {
				select {
				case client.send <- msg.message: // non-blocking send
				default:
					// Client's send buffer is full — they're too slow, disconnect
					close(client.send)
					h.mu.Lock()
					delete(h.sessions[msg.sessionID], client)
					h.mu.Unlock()
				}
			}
		}
	}
}

// Broadcast sends a typed message to all clients in a session
func (h *Hub) Broadcast(sessionID string, msgType WSMessageType, payload interface{}) {
	msg := WSMessage{Type: msgType, Payload: payload}
	data, err := json.Marshal(msg)
	if err != nil {
		log.Printf("Hub.Broadcast marshal error: %v", err)
		return
	}
	h.broadcast <- broadcastMsg{sessionID: sessionID, message: data}
}

// ── HTTP handler: upgrade to WebSocket ───────────────────────
func (h *Hub) ServeWS(w http.ResponseWriter, r *http.Request) {
	// Get session ID from URL: /ws/{sessionID}
	sessionID := r.URL.Query().Get("session_id")
	if sessionID == "" {
		http.Error(w, "session_id required", http.StatusBadRequest)
		return
	}

	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WS upgrade error: %v", err)
		return
	}

	client := &Client{
		sessionID: sessionID,
		conn:      conn,
		send:      make(chan []byte, 256),
	}

	h.register <- client

	// LESSON: goroutines
	// `go` starts a function in a new goroutine — non-blocking.
	// We start two goroutines per client:
	//   writePump: sends messages from client.send channel → WebSocket
	//   readPump:  reads from WebSocket (handles pings, detects disconnect)
	go client.writePump(h)
	go client.readPump(h)
}

// writePump sends queued messages to the WebSocket connection
func (c *Client) writePump(h *Hub) {
	defer c.conn.Close()

	for message := range c.send {
		// range over a channel blocks until a message arrives or channel closes
		if err := c.conn.WriteMessage(websocket.TextMessage, message); err != nil {
			return
		}
	}
}

// readPump reads from WebSocket — detects disconnection
func (c *Client) readPump(h *Hub) {
	defer func() {
		h.unregister <- c
		c.conn.Close()
	}()

	for {
		_, _, err := c.conn.ReadMessage()
		if err != nil {
			// Connection closed or error — unregister and exit
			break
		}
		// We don't expect messages from Flutter in this version
		// (Flutter only listens, doesn't send via WebSocket)
	}
}
