
from guillotina import testing
from guillotina_rediscache.tests.docker_redis import redis_image

import pytest


def settings_configurator(settings):
    if 'applications' in settings:
        settings['applications'].append('guillotina_rediscache')
    else:
        settings['applications'] = ['guillotina_rediscache']
    del settings['static']
    del settings['jsapps']


testing.configure_with(settings_configurator)


@pytest.fixture(scope='session')
def redis():
    """
    detect travis, use travis's postgres; otherwise, use docker
    """
    host = redis_image.run()

    yield host  # provide the fixture value

    redis_image.stop()
