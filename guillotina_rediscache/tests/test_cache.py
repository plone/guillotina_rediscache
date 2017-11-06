from guillotina import app_settings
from guillotina.component import getUtility
from guillotina.tests import mocks
from guillotina.tests.utils import create_content
from guillotina_rediscache import cache
from guillotina_rediscache import serialize
from guillotina_rediscache.cache_strategy import RedisCache
from guillotina_rediscache.interfaces import CACHE_PREFIX
from guillotina_rediscache.interfaces import IRedisChannelUtility

import asyncio


async def test_cache_set(redis, dummy_guillotina, loop):
    await cache.close_redis_pool()
    trns = mocks.MockTransaction(mocks.MockTransactionManager())
    trns.added = trns.deleted = {}
    rcache = RedisCache(trns, loop=loop)
    await rcache.clear()

    await rcache.set('bar', oid='foo')
    # make sure it is in redis
    assert serialize.loads(await rcache._redis.get(CACHE_PREFIX + 'foo')) == "bar"
    # but also in memory
    assert rcache._memory_cache.get('foo') == 'bar'
    # and api matches..
    assert await rcache.get(oid='foo') == 'bar'

    await cache.close_redis_pool()


async def test_cache_delete(redis, dummy_guillotina, loop):
    await cache.close_redis_pool()
    trns = mocks.MockTransaction(mocks.MockTransactionManager())
    trns.added = trns.deleted = {}
    rcache = RedisCache(trns, loop=loop)
    await rcache.clear()

    await rcache.set('bar', oid='foo')
    # make sure it is in redis
    assert serialize.loads(await rcache._redis.get(CACHE_PREFIX + 'foo')) == "bar"
    assert rcache._memory_cache.get('foo') == 'bar'
    assert await rcache.get(oid='foo') == 'bar'

    # now delete
    await rcache.delete('foo')
    assert await rcache.get(oid='foo') is None

    await cache.close_redis_pool()


async def test_cache_clear(redis, dummy_guillotina, loop):
    await cache.close_redis_pool()
    trns = mocks.MockTransaction(mocks.MockTransactionManager())
    trns.added = trns.deleted = {}
    rcache = RedisCache(trns, loop=loop)
    await rcache.clear()

    await rcache.set('bar', oid='foo')
    # make sure it is in redis
    assert serialize.loads(await rcache._redis.get(CACHE_PREFIX + 'foo')) == "bar"
    assert rcache._memory_cache.get('foo') == 'bar'
    assert await rcache.get(oid='foo') == 'bar'

    await rcache.clear()
    assert await rcache.get(oid='foo') is None

    await cache.close_redis_pool()


async def test_invalidate_object(redis, dummy_guillotina, loop):
    await cache.close_redis_pool()
    trns = mocks.MockTransaction(mocks.MockTransactionManager())
    trns.added = trns.deleted = {}
    content = create_content()
    trns.modified = {content._p_oid: content}
    rcache = RedisCache(trns, loop=loop)
    await rcache.clear()

    await rcache.set('foobar', oid=content._p_oid)
    assert serialize.loads(await rcache._redis.get(CACHE_PREFIX + content._p_oid)) == "foobar"
    assert rcache._memory_cache.get(content._p_oid) == 'foobar'
    assert await rcache.get(oid=content._p_oid) == 'foobar'

    await rcache.close(invalidate=True)
    assert await rcache.get(oid=content._p_oid) is None

    await cache.close_redis_pool()


async def test_subscriber_invalidates(redis, dummy_guillotina, loop):
    await cache.close_redis_pool()
    trns = mocks.MockTransaction(mocks.MockTransactionManager())
    trns.added = trns.deleted = {}
    content = create_content()
    trns.modified = {content._p_oid: content}
    rcache = RedisCache(trns, loop=loop)
    await rcache.clear()

    await rcache.set('foobar', oid=content._p_oid)
    assert serialize.loads(await rcache._redis.get(CACHE_PREFIX + content._p_oid)) == "foobar"
    assert rcache._memory_cache.get(content._p_oid) == 'foobar'
    assert await rcache.get(oid=content._p_oid) == 'foobar'

    assert content._p_oid in rcache._memory_cache

    await rcache._redis.publish_json(app_settings['redis']['updates_channel'], {
        'tid': 32423,
        'keys': [content._p_oid]
    })
    await asyncio.sleep(1)  # should be enough for pub/sub to finish
    assert content._p_oid not in rcache._memory_cache

    await cache.close_redis_pool()


async def test_subscriber_ignores_trsn_on_invalidate(redis, dummy_guillotina, loop):
    await cache.close_redis_pool()
    trns = mocks.MockTransaction(mocks.MockTransactionManager())
    trns.added = trns.deleted = {}
    content = create_content()
    trns.modified = {content._p_oid: content}
    rcache = RedisCache(trns, loop=loop)
    await rcache.clear()

    await rcache.set('foobar', oid=content._p_oid)
    assert serialize.loads(await rcache._redis.get(CACHE_PREFIX + content._p_oid)) == "foobar"
    assert rcache._memory_cache.get(content._p_oid) == 'foobar'
    assert await rcache.get(oid=content._p_oid) == 'foobar'

    assert content._p_oid in rcache._memory_cache

    utility = getUtility(IRedisChannelUtility)
    utility.ignore_tid(5555)

    await rcache._redis.publish_json(app_settings['redis']['updates_channel'], {
        'tid': 5555,
        'keys': [content._p_oid]
    })
    await asyncio.sleep(1)  # should be enough for pub/sub to finish
    # should still be there because we set to ignore this tid
    assert content._p_oid in rcache._memory_cache
    # tid should also now be removed from ignored list
    assert 5555 not in utility._ignored_tids

    await cache.close_redis_pool()
