# services/database.py
import asyncpg
from pgvector.asyncpg import register_vector
from config import get_settings

settings = get_settings()

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=2,
            max_size=10,
            init=_init_connection,
        )
    return _pool


async def _init_connection(conn: asyncpg.Connection) -> None:
    # Set search path to include public schema explicitly
    await conn.execute("SET search_path TO public")
    # Register pgvector codec
    try:
        await register_vector(conn)
    except Exception:
        # Fallback: register manually if extension is in public schema
        await conn.execute("SET search_path TO public, pg_catalog")
        await register_vector(conn)


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


from contextlib import asynccontextmanager

@asynccontextmanager
async def db_conn():
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn
