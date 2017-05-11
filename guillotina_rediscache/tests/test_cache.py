from guillotina_rediscache.cache_strategy import RedisCache
from guillotina.tests import mocks
from guillotina_rediscache import cache
from guillotina.tests.utils import create_content


async def test_cache_set(redis, dummy_guillotina, loop):
    await cache.close_redis_pool()
    rcache = RedisCache(mocks.MockStorage(), mocks.MockTransaction(), loop=loop)
    await rcache.clear()

    await rcache.set('bar', oid='foo')
    # make sure it is in redis
    assert await rcache._conn.get('foo') == b'"bar"'
    # but also in memory
    assert rcache._memory_cache.get('foo') == 'bar'
    # and api matches..
    assert await rcache.get(oid='foo') == 'bar'

    await cache.close_redis_pool()


async def test_cache_delete(redis, dummy_guillotina, loop):
    await cache.close_redis_pool()
    rcache = RedisCache(mocks.MockStorage(), mocks.MockTransaction(), loop=loop)
    await rcache.clear()

    await rcache.set('bar', oid='foo')
    # make sure it is in redis
    assert await rcache._conn.get('foo') == b'"bar"'
    assert rcache._memory_cache.get('foo') == 'bar'
    assert await rcache.get(oid='foo') == 'bar'

    # now delete
    await rcache.delete('foo')
    assert await rcache.get(oid='foo') is None

    await cache.close_redis_pool()


async def test_cache_clear(redis, dummy_guillotina, loop):
    await cache.close_redis_pool()
    rcache = RedisCache(mocks.MockStorage(), mocks.MockTransaction(), loop=loop)
    await rcache.clear()

    await rcache.set('bar', oid='foo')
    # make sure it is in redis
    assert await rcache._conn.get('foo') == b'"bar"'
    assert rcache._memory_cache.get('foo') == 'bar'
    assert await rcache.get(oid='foo') == 'bar'

    await rcache.clear()
    assert await rcache.get(oid='foo') is None

    await cache.close_redis_pool()


async def test_invalidate_object(redis, dummy_guillotina, loop):
    await cache.close_redis_pool()
    trns = mocks.MockTransaction()
    content = create_content()
    trns.modified = {content._p_oid: content}
    rcache = RedisCache(mocks.MockStorage(), trns, loop=loop)
    await rcache.clear()

    await rcache.set('foobar', oid=content._p_oid)
    assert await rcache._conn.get(content._p_oid) == b'"foobar"'
    assert rcache._memory_cache.get(content._p_oid) == 'foobar'
    assert await rcache.get(oid=content._p_oid) == 'foobar'

    await rcache.close(invalidate=True)
    assert await rcache.get(oid=content._p_oid) is None

    await cache.close_redis_pool()
