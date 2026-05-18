# services/database.py
#
# LESSON: async/await + connection pools
#
# "async" means: while waiting for the database to respond,
# Python doesn't freeze — it handles other requests instead.
# This is critical for a debate app where multiple parties
# might submit arguments at the same time.
#
# A "connection pool" is a pre-opened set of database connections
# that get reused. Opening a fresh connection for every request
# is slow (it's a TCP handshake + auth round trip). A pool of 10
# connections handles hundreds of requests per second by reusing them.

import asyncpg
from pgvector.asyncpg import register_vector
from config import get_settings

settings = get_settings()

# Module-level pool — shared across the whole app lifetime
_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Return the shared connection pool, creating it on first call."""
    global _pool

    if _pool is None:
        # init sets up pgvector support on every new connection
        _pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=2,   # always keep 2 connections warm
            max_size=10,  # scale up to 10 under load
            init=_init_connection,
        )
    return _pool


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Called once per connection when it's first created."""
    # Register pgvector codec so asyncpg knows how to read/write vector columns
    await register_vector(conn)


async def close_pool() -> None:
    """Gracefully close all connections on app shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ── Helper: get a single connection from the pool ────────────
# Use this as an async context manager:
#   async with db_conn() as conn:
#       rows = await conn.fetch("SELECT ...")
# The connection is automatically returned to the pool when the block exits

from contextlib import asynccontextmanager

@asynccontextmanager
async def db_conn():
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn   # 'conn' is available inside the 'async with' block
