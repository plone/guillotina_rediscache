from guillotina import app_settings
from guillotina import configure
from guillotina.component import getUtility
from guillotina.db.cache.base import BaseCache
from guillotina.db.interfaces import IStorageCache
from guillotina.db.interfaces import ITransaction
from guillotina_rediscache import cache
from guillotina_rediscache import serialize
from guillotina_rediscache.interfaces import CACHE_PREFIX
from guillotina_rediscache.interfaces import IRedisChannelUtility

import aioredis
import logging


logger = logging.getLogger('guillotina_rediscache')


@configure.adapter(for_=ITransaction, provides=IStorageCache,
                   name="redis")
class RedisCache(BaseCache):

    def __init__(self, transaction, loop=None):
        super().__init__(transaction)
        self._loop = loop

        self._conn = None
        self._redis = None
        self._memory_cache = cache.get_memory_cache()
        self._settings = app_settings.get('redis', {})

        self._keys_to_invalidate = []

    async def get_conn(self):
        if self._conn is None:
            self._conn = await (await cache.get_redis_pool(self._loop)).acquire()
        return self._conn

    async def get_redis(self):
        if self._redis is None:
            self._redis = aioredis.Redis(await self.get_conn())
        return self._redis

    async def get(self, **kwargs):
        key = self.get_key(**kwargs)
        try:
            if key in self._memory_cache:
                logger.info('Retrieved {} from memory cache'.format(key))
                return self._memory_cache[key]
            conn = await self.get_redis()
            val = await conn.get(CACHE_PREFIX + key)
            if val is not None:
                logger.info('Retrieved {} from redis cache'.format(key))
                val = serialize.loads(val)
                self._memory_cache[key] = val
            return val
        except Exception:
            logger.warning('Error getting cache value', exc_info=True)

    async def set(self, value, **kwargs):
        key = self.get_key(**kwargs)
        try:
            conn = await self.get_redis()
            self._memory_cache[key] = value
            await conn.set(CACHE_PREFIX + key, serialize.dumps(value),
                           expire=self._settings.get('ttl', 3600))
            logger.info('set {} in cache'.format(key))
        except Exception:
            logger.warning('Error setting cache value', exc_info=True)

    async def clear(self):
        try:
            self._memory_cache.clear()
            conn = await self.get_redis()
            await conn.flushall()
            logger.info('Cleared cache')
        except Exception:
            logger.warning('Error clearing cache', exc_info=True)

    async def delete(self, key):
        self._keys_to_invalidate.append(key)
        try:
            conn = await self.get_redis()
            if key in self._memory_cache:
                del self._memory_cache[key]
            await conn.delete(CACHE_PREFIX + key)
            logger.info('Deleted cache key {}'.format(key))
        except:
            logger.warning('Error deleting cache key {}'.format(key), exc_info=True)

    async def delete_all(self, keys):
        for key in keys:
            await self.delete(key)

    async def _invalidate_keys(self, data, type_):
        invalidated = []
        for oid, ob in data.items():
            for key in self.get_cache_keys(ob, type_):
                invalidated.append(key)
                await self.delete(key)
                if key in self._memory_cache:
                    del self._memory_cache[key]
        return invalidated

    async def close(self, invalidate=True):
        try:
            if self._conn is None:
                if not invalidate:
                    # skip out, nothing to do
                    return
                await self.get_redis()  # force getting connnection object

            if invalidate:
                await self._invalidate_keys(self._transaction.modified, 'modified')
                await self._invalidate_keys(self._transaction.added, 'added')
                await self._invalidate_keys(self._transaction.deleted, 'deleted')

            await self._synchronize_and_close()

        except Exception:
            logger.warning('Error closing connection', exc_info=True)

    async def _synchronize_and_close(self):
        '''
        publish cache changes on redis
        '''
        if len(self._keys_to_invalidate) > 0:
            channel_utility = getUtility(IRedisChannelUtility)
            channel_utility.ignore_tid(self._transaction._tid)
            await self._redis.publish_json(self._settings['updates_channel'], {
                'tid': self._transaction._tid,
                'keys': self._keys_to_invalidate
            })

        await self._close()

    async def _close(self, keys=[]):
        try:
            self._keys_to_invalidate = []
            pool = await cache.get_redis_pool(self._loop)
            if self._conn is not None and self._conn in pool._used:
                pool.release(self._conn)
        except Exception:
            logger.warning('Error closing cache connection', exc_info=True)
