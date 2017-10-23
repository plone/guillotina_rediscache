from guillotina import app_settings
from lru import LRU

import aioredis
import threading


# guillotina is single threaded, we just want a global that is mutable
# to storage the redis connection pool
_local = threading.local()


async def close_redis_pool():
    if hasattr(_local, 'redis_pool'):
        pool = _local.redis_pool
        try:
            await pool.clear()
        except RuntimeError:
            pass
        del _local.redis_pool


async def get_redis_pool(loop=None):
    if not hasattr(_local, 'redis_pool'):
        settings = app_settings['redis']
        _local.redis_pool = await aioredis.create_pool(
            (settings['host'], settings['port']),
            **settings['pool'],
            loop=loop)
    return _local.redis_pool


def get_memory_cache():
    if not hasattr(_local, 'lru'):
        settings = app_settings['redis']
        _local.lru = LRU(settings['memory_cache_size'])
    return _local.lru
