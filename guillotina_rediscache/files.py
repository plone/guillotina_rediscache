from guillotina.files.adapter import DBDataManager
from guillotina.renderers import GuillotinaJSONEncoder
from guillotina_rediscache import cache

import aioredis
import json
import time


class RedisFileDataManager(DBDataManager):

    _redis = None
    _data = None
    _loaded = False
    _ttl = 60 * 50 * 5  # 5 minutes should be plenty of time between activity

    async def load(self):
        # preload data
        if self._data is None:
            redis = await self.get_redis()
            key = await self.get_key()
            data = await redis.get(key)
            if not data:
                self._data = {}
            else:
                self._loaded = True
                self._data = json.loads(data)

    async def start(self):
        self.protect()

        self._data.clear()
        self._data['last_activity'] = time.time()
        if self._loaded:
            await self.save()

    async def save(self):
        redis = await self.get_redis()
        key = await self.get_key()
        await redis.set(key, json.dumps(self._data, cls=GuillotinaJSONEncoder))
        await redis.expire(key, self._ttl)

    async def get_redis(self):
        if self._redis is None:
            conn = await cache.get_redis_pool()
            self._redis = aioredis.Redis(conn)
        return self._redis

    async def get_key(self):
        # only need 1 write to save upload object id...
        return '{}-{}'.format(
            self.context._p_oid,
            self.field.__name__
        )

    async def update(self, **kwargs):
        self._data.update(kwargs)
        await self.save()

    async def finish(self, values=None):
        await super().finish(values=values)
        # and clear the cache key
        redis = await self.get_redis()
        key = await self.get_key()
        await redis.delete(key)
