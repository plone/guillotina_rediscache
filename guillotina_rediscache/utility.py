from guillotina import app_settings
from guillotina import configure
from guillotina.profile import profilable
from guillotina_rediscache import cache
from guillotina_rediscache import serialize
from guillotina_rediscache.interfaces import IRedisChannelUtility

import aioredis
import asyncio
import logging
import pickle


logger = logging.getLogger('guillotina_rediscache')


@configure.utility(provides=IRedisChannelUtility)
class RedisChannelUtility:

    def __init__(self, settings=None, loop=None):
        self._loop = loop
        self._settings = {}
        self._ignored_tids = []
        self._pool = None
        self._redis = None

    @profilable
    async def initialize(self, app=None):
        settings = app_settings['redis']
        while True:
            try:
                self._pool = await cache.get_redis_pool(self._loop)
                self._redis = aioredis.Redis(self._pool)
                res = await self._redis.subscribe(settings['updates_channel'])
                ch = res[0]
                while (await ch.wait_message()):
                    try:
                        msg = serialize.loads(await ch.get())
                        await self.invalidate(msg)
                    except (TypeError, pickle.UnpicklingError):
                        pass
            except (asyncio.CancelledError, RuntimeError):
                # task cancelled, let it die
                return
            except Exception:
                logger.warn(
                    'Error subscribing to redis changes. Waiting before trying again',
                    exc_info=True)
                await asyncio.sleep(5)

    async def finalize(self, app):
        settings = app_settings['redis']
        if self._redis is not None:
            try:
                await self._redis.unsubscribe(settings['updates_channel'])
                await cache.close_redis_pool()
            except (asyncio.CancelledError, RuntimeError):
                # task cancelled, let it die
                return

    @profilable
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

        for cache_key, ob in data.get('push', {}).items():
            mem_cache[cache_key] = ob

    def ignore_tid(self, tid):
        # so we don't invalidate twice...
        self._ignored_tids.append(tid)
