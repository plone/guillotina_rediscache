from guillotina import testing
from guillotina_rediscache.tests.docker_redis import redis_image

import os
import pytest


def settings_configurator(settings):
    if 'applications' in settings:
        settings['applications'].append('guillotina_rediscache')
    else:
        settings['applications'] = ['guillotina_rediscache']
    del settings['static']
    del settings['jsapps']
    settings["redis"] = {
        'host': getattr(redis, 'host', 'localhost'),
        'port': getattr(redis, 'port', 6379),
        'ttl': 3600,
        'memory_cache_size': 1000,
        'updates_channel': 'guillotina',
        'pool': {
            'minsize': 5,
            'maxsize': 100
        }
    }


testing.configure_with(settings_configurator)


@pytest.fixture(scope='session')
def redis():
    """
    detect travis, use travis's postgres; otherwise, use docker
    """
    if 'TRAVIS' in os.environ:
        host = 'localhost'
        port = 6379
    else:
        host, port = redis_image.run()

    setattr(redis, 'host', host)
    setattr(redis, 'port', port)

    yield host, port  # provide the fixture value

    if 'TRAVIS' not in os.environ:
        redis_image.stop()
