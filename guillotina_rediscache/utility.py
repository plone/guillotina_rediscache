from guillotina import app_settings
from guillotina import configure
from guillotina_rediscache import cache
from guillotina_rediscache.interfaces import IRedisChannelUtility

import aioredis
import asyncio
import logging
import ujson


logger = logging.getLogger('guillotina_rediscache')


@configure.utility(provides=IRedisChannelUtility)
class RedisChannelUtility:

    def __init__(self, settings=None, loop=None):
        self._loop = loop
        self._settings = {}
        self._ignored_tids = []
        self._pool = None
        self._conn = None
        self._redis = None

    async def initialize(self, app=None):
        settings = app_settings['redis']
        while True:
            try:
                self._pool = await cache.get_redis_pool(self._loop)
                self._conn = await self._pool.acquire()
                self._redis = aioredis.Redis(self._conn)
                res = await self._redis.subscribe(settings['updates_channel'])
                ch = res[0]
                while (await ch.wait_message()):
                    msg = ujson.loads(await ch.get(encoding='utf-8'))
                    await self.invalidate(msg)
            except asyncio.CancelledError:
                # task cancelled, let it die
                pass
            except Exception:
                try:
                    self._pool.release(self._conn)
                except (AttributeError, RuntimeError):
                    pass
                logger.warn(
                    'Error subscribing to redis changes. Waiting before trying again',
                    exc_info=True)
                await asyncio.sleep(5)

    async def finalize(self, app):
        settings = app_settings['redis']
        if self._conn is not None and self._redis is not None:
            await self._redis.unsubscribe(settings['updates_channel'])
        await cache.close_redis_pool()

    async def invalidate(self, data):
        assert isinstance(data, dict)
        assert 'tid' in data
        assert 'keys' in data
        if data['tid'] in self._ignored_tids:
            # on the same thread, ignore this sucker...
            self._ignored_tids.remove(data['tid'])
            return
        mem_cache = cache.get_memory_cache()
        for key in data['keys']:
            if key in mem_cache:
                del mem_cache[key]

    def ignore_tid(self, tid):
        # so we don't invalidate twice...
        self._ignored_tids.append(tid)
