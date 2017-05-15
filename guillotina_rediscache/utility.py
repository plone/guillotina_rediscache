from guillotina import app_settings
from guillotina import configure
from guillotina_rediscache import cache
from guillotina_rediscache.interfaces import IRedisChannelUtility

import asyncio
import logging


logger = logging.getLogger('guillotina_rediscache')


@configure.utility(provides=IRedisChannelUtility)
class RedisChannelUtility:

    def __init__(self, settings=None, loop=None):
        self._loop = loop
        self._settings = {}
        self._ignored_tids = []
        self._pool = None
        self._conn = None

    async def initialize(self, app=None):
        settings = app_settings['redis']
        while True:
            try:
                self._pool = await cache.get_redis_pool(self._loop)
                self._conn = await self._pool.acquire()
                res = await self._conn.subscribe(settings['updates_channel'])
                ch = res[0]
                while (await ch.wait_message()):
                    msg = await ch.get_json()
                    await self.invalidate(msg)
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
        if self._conn is not None:
            await self._conn.unsubscribe(settings['updates_channel'])
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


# unused right now, for some reason it's slower this way? maybe because we
# get more conflicts
# @configure.utility(provides=IRedisUtility)
class RedisUtility:

    def __init__(self, settings=None, loop=None):
        self._loop = loop
        self._settings = {}
        self._conn = None
        self._pool = None

    async def get_pool(self):
        if self._pool is None:
            self._pool = await cache.get_redis_pool(self._loop)
        return self._pool

    async def get_conn(self):
        if self._conn is None:
            pool = await self.get_pool()
            self._conn = await pool.acquire()
        return self._conn

    async def initialize(self, app=None):
        self._queue = asyncio.Queue()

        while True:
            try:
                _type, group = await self._queue.get()
                conn = await self.get_conn()
                if _type == 'delete':
                    for key in group:
                        await conn.delete(key)
            except Exception:
                logger.warn(
                    'Error invalidating queue',
                    exc_info=True)
                await asyncio.sleep(1)

    async def finalize(self, app):
        pass

    async def push_deletes(self, keys):
        await self._queue.put(('delete', keys))
