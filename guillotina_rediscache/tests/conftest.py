from guillotina.testing import TESTING_SETTINGS
from guillotina_rediscache.tests.docker_redis import redis_image

import pytest


if 'applications' in TESTING_SETTINGS:
    TESTING_SETTINGS['applications'].append('guillotina_rediscache')
else:
    TESTING_SETTINGS['applications'] = ['guillotina_rediscache']


@pytest.fixture(scope='session')
def redis():
    """
    detect travis, use travis's postgres; otherwise, use docker
    """
    host = redis_image.run()

    yield host  # provide the fixture value

    redis_image.stop()


from guillotina.tests.conftest import *  # noqa
