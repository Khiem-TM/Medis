from redis.asyncio import Redis, ConnectionPool
from app.config import settings

_pool: ConnectionPool | None = None

def get_redis_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=20,  # Giới hạn số kết nối đồng thời
            decode_responses=True,  # Tự decode bytes --> String
        )
    return _pool

async def get_redis() -> Redis:
    pool = get_redis_pool()
    client = Redis(connection_pool=pool)   
    try:
        yield client
    finally:
        await client.close()  # Đóng kết nối sau khi xong việc