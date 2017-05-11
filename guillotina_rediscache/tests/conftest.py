from guillotina.testing import TESTING_SETTINGS
from guillotina_rediscache.tests.docker_redis import run_docker_redis
from guillotina_rediscache.tests.docker_redis import cleanup_redis_docker
import pytest

if 'applications' in TESTING_SETTINGS:
    TESTING_SETTINGS['applications'].append('guillotina_rediscache')
else:
    TESTING_SETTINGS['applications'] = ['guillotina_rediscache']

from guillotina.tests.conftest import *  # noqa


@pytest.fixture(scope='session')
def redis():
    """
    detect travis, use travis's postgres; otherwise, use docker
    """
    host = run_docker_redis()

    yield host  # provide the fixture value

    cleanup_redis_docker()
