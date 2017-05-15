from guillotina import configure
from guillotina.interfaces import IContainer
from guillotina_rediscache import cache


@configure.service(context=IContainer, name='@redis-cache-stats', method='GET',
                   permission='guillotina_rediscache.Manage')
async def stats(context, request):
    memory_cache = cache.get_memory_cache()

    pool = await cache.get_redis_pool()
    conn = await pool.acquire()
    redis_data = await conn.info()
    pool.release(conn)
    return {
        'in-memory': {
            'size': len(memory_cache),
            'stats': memory_cache.get_stats()
        },
        'redis': redis_data
    }


@configure.service(context=IContainer, name='@redis-cache-clear', method='POST',
                   permission='guillotina_rediscache.Manage')
async def clear(context, request):
    memory_cache = cache.get_memory_cache()
    memory_cache.clear()
    pool = await cache.get_redis_pool()
    conn = await pool.acquire()
    await conn.flushall()
    pool.release(conn)
    return {
        'success': True
    }
