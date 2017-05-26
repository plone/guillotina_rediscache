from guillotina import app_settings
from guillotina import configure
from guillotina.component import getUtility
from guillotina.db.cache.base import BaseCache
from guillotina.db.interfaces import IStorage
from guillotina.db.interfaces import IStorageCache
from guillotina.db.interfaces import ITransaction
from guillotina_rediscache import cache
from guillotina_rediscache import serialize
from guillotina_rediscache.interfaces import IRedisChannelUtility

import logging


logger = logging.getLogger('guillotina_rediscache')


@configure.adapter(for_=(IStorage, ITransaction), provides=IStorageCache,
                   name="redis")
class RedisCache(BaseCache):

    def __init__(self, storage, transaction, loop=None):
        self._storage = storage
        self._transaction = transaction
        self._loop = loop

        self._conn = None
        self._memory_cache = cache.get_memory_cache()
        self._settings = app_settings.get('redis', {})

        # self._utility = getUtility(IRedisUtility)

    async def get_conn(self):
        if self._conn is None:
            self._conn = await (await cache.get_redis_pool(self._loop)).acquire()
        return self._conn

    async def get(self, **kwargs):
        key = self.get_key(**kwargs)
        try:
            if key in self._memory_cache:
                logger.info('Retrieved {} from memory cache'.format(key))
                return self._memory_cache[key]
            conn = await self.get_conn()
            val = await conn.get(key)
            if val is not None:
                logger.info('Retrieved {} from redis cache'.format(key))
                val = serialize.loads(val)
                self._memory_cache[key] = val
            return val
        except Exception:
            logger.warn('Error getting cache value', exc_info=True)

    async def set(self, value, **kwargs):
        key = self.get_key(**kwargs)
        try:
            conn = await self.get_conn()
            self._memory_cache[key] = value
            await conn.set(key, serialize.dumps(value),
                           expire=self._settings.get('ttl', 3600))
            logger.info('set {} in cache'.format(key))
        except Exception:
            logger.warn('Error setting cache value', exc_info=True)

    async def clear(self):
        try:
            self._memory_cache.clear()
            conn = await self.get_conn()
            await conn.flushall()
            logger.info('Cleared cache')
        except Exception:
            logger.warn('Error clearing cache', exc_info=True)

    async def delete(self, key):
        try:
            conn = await self.get_conn()
            if key in self._memory_cache:
                del self._memory_cache[key]
            await conn.delete(key)
            logger.info('Deleted cache key {}'.format(key))
        except:
            logger.warn('Error deleting cache key {}'.format(key), exc_info=True)

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
                self._conn = await (await cache.get_redis_pool(self._loop)).acquire()

            keys = []
            if invalidate:
                keys.extend(await self._invalidate_keys(
                    self._transaction.modified, 'modified'))
                keys.extend(await self._invalidate_keys(
                    self._transaction.added, 'added'))
                keys.extend(await self._invalidate_keys(
                    self._transaction.deleted, 'deleted'))

            if len(keys) > 0:
                channel_utility = getUtility(IRedisChannelUtility)
                channel_utility.ignore_tid(self._transaction._tid)

                await self._conn.publish_json(self._settings['updates_channel'], {
                    'tid': self._transaction._tid,
                    'keys': keys
                })

            await self._close(keys)

        except Exception:
            logger.warn('Error closing connection', exc_info=True)

    async def _close(self, keys=[]):
        try:
            pool = await cache.get_redis_pool(self._loop)
            if self._conn in pool._used:
                pool.release(self._conn)
        except Exception:
            logger.warn('Error closing cache connection', exc_info=True)
