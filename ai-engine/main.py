# main.py
#
# LESSON: FastAPI app lifecycle
#
# FastAPI uses "lifespan" to run code on startup and shutdown.
# This is where you open DB pools, load ML models, warm caches —
# anything that should happen ONCE at boot, not on every request.

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.argument import router as argument_router
from routers.argument import session_router
from routers.exchange import router as exchange_router
from services.database import get_pool, close_pool


# ── Lifespan: startup + shutdown ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    print("🔌 Connecting to panel database...")
    await get_pool()           # creates the connection pool once
    print("✅ AI Engine ready")

    yield   # app runs here — everything above is "startup", below is "shutdown"

    # --- SHUTDOWN ---
    print("🔌 Closing database connections...")
    await close_pool()


# ── Create the app ────────────────────────────────────────────
app = FastAPI(
    title="lioMalau AI Engine",
    description="Argument parsing, RAG retrieval, and adjudication service",
    version="0.1.0",
    lifespan=lifespan,
    # docs_url="/docs" — FastAPI auto-generates interactive API docs here
    # Try it: http://localhost:8001/docs after `docker-compose up`
)


# ── CORS middleware ───────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing) controls which origins can call this API.
# During development we allow everything. In production, restrict to your domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # lock this down in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Mount routers ─────────────────────────────────────────────
# Each router handles a group of related endpoints.
# prefix="/api/v1" means all routes become /api/v1/arguments/... etc.
app.include_router(argument_router, prefix="/api/v1")
app.include_router(session_router,  prefix="/api/v1")
app.include_router(exchange_router, prefix="/api/v1")


# ── Health check ─────────────────────────────────────────────
# Every service should have a /health endpoint.
# Docker, load balancers, and monitoring tools ping this to check if
# the service is alive. Return 200 = healthy, anything else = alert.
@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "liomalau-ai-engine"}


# ── Root ──────────────────────────────────────────────────────
@app.get("/", tags=["system"])
async def root():
    return {
        "service": "lioMalau AI Engine",
        "docs": "/docs",
        "endpoints": {
            "submit_argument": "POST /api/v1/arguments/",
            "create_session":  "POST /api/v1/sessions/",
            "get_scores":      "GET  /api/v1/sessions/{id}/scores",
        }
    }
