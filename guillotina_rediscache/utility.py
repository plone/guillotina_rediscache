from aioredis.abc import AbcChannel
from aioredis.pubsub import Receiver
from guillotina import app_settings
from guillotina import configure
from guillotina_rediscache import cache
from guillotina_rediscache.interfaces import IRedisUtility

import asyncio
import logging


logger = logging.getLogger('guillotina_rediscache')


@configure.utility(provides=IRedisUtility)
class RedisUtility:

    def __init__(self, settings=None, loop=None):
        self._loop = loop
        self._settings = {}
        self._pool = None
        self._conn = None

    async def reader(self, mpsc):
        async for channel, msg in mpsc.iter():
            assert isinstance(channel, AbcChannel)
            print("Got {!r} in channel {!r}".format(msg, channel))

    async def initialize(self, app=None):
        settings = app_settings['redis']
        while True:
            try:
                mpsc = Receiver(loop=self._loop)
                await self.reader(mpsc)
                self._pool = await cache.get_redis_pool(self._loop)
                self._conn = await self._pool.acquire()
                await self._conn.subscribe(mpsc.channel(settings['updates_channel']))
            except Exception:
                logger.warn(
                    'Error subscribing to redis changes. Waiting before trying again',
                    exc_info=True)
                await asyncio.sleep(5)

    async def finalize(self):
        await cache.close_redis_pool()
