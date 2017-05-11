from guillotina import configure, app_settings
from guillotina.db.cache.base import BaseCache
from guillotina.db.interfaces import IStorage
from guillotina.db.interfaces import IStorageCache
from guillotina.db.interfaces import ITransaction
from guillotina_rediscache import cache
from guillotina_rediscache import serialize

import asyncio
import logging


logger = logging.getLogger('guillotina_rediscache')


@configure.adapter(for_=(IStorage, ITransaction), provides=IStorageCache,
                   name="redis")
class RedisCache(BaseCache):

    def __init__(self, storage, transaction):
        self._storage = storage
        self._transaction = transaction
        self._conn = None
        self._memory_cache = cache.get_memory_cache()

    async def get_conn(self):
        if self._conn is None:
            self._conn = await (await cache.get_redis_pool()).acquire()
        return self._conn

    async def get(self, **kwargs):
        key = self.get_key(**kwargs)
        try:
            if key in self._memory_cache:
                logger.debug('Retrieved {} from memory cache'.format(key))
                return self._memory_cache[key]
            conn = await self.get_conn()
            val = await conn.get(key)
            if val is not None:
                logger.debug('Retrieved {} from redis cache'.format(key))
                val = serialize.loads(val)
                self._memory_cache[key] = val
            return val
        except Exception:
            logger.warn('Error getting cache value', exc_info=True)

    async def set(self, value, **kwargs):
        key = self.get_key(**kwargs)
        try:
            conn = await self.get_conn()
            value = serialize.dumps(value)
            self._memory_cache[key] = value
            await conn.set(key, value,
                           expire=app_settings.get('redis', {}).get('ttl', 3600))
            logger.debug('set {} in cache'.format(key))
        except Exception:
            logger.warn('Error setting cache value', exc_info=True)

    async def clear(self):
        try:
            self._memory_cache.clear()
            conn = await self.get_conn()
            await conn.clear()
            logger.debug('Cleared cache')
        except Exception:
            logger.warn('Error clearing cache', exc_info=True)

    async def delete(self, key):
        try:
            conn = await self.get_conn()
            if key in self._memory_cache:
                del self._memory_cache[key]
            await conn.delete(key)
            logger.debug('Deleted cache key {}'.format(key))
        except:
            logger.warn('Error deleting cache key {}'.format(key), exc_info=True)

    async def delete_all(self, keys):
        for key in keys:
            await self.delete(key)

    async def close(self, invalidate=False):
        try:
            if self._conn is None:
                if (len(self._transaction.objects_needing_invalidation) == 0 or
                        not invalidate):
                    return
                self._conn = await (await cache.get_redis_pool()).acquire()

            if invalidate:
                batch = []
                # now work ob invalidations...
                # we only care about modified objects because:
                #   - deleted objects will expire on their own
                #   - added objects are not in the cache yet...
                for oid, ob in self._transaction.modified.items():
                    for key in self.get_cache_keys(ob):
                        if key in self._memory_cache:
                            del self._memory_cache[key]
                        batch.append(self.delete(key))
                        if len(batch) >= 10:
                            await asyncio.gather(*batch)
                            batch = []
                if len(batch) >= 0:
                    await asyncio.gather(*batch)

            cpool = await cache.get_redis_pool()
            cpool.release(self._conn)
        except Exception:
            logger.warn('Error closing cache connection', exc_info=True)
