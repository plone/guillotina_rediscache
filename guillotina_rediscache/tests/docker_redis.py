from guillotina.tests.docker_containers.base import BaseImage
from time import sleep


class Redis(BaseImage):
    label = 'redis'
    image = 'redis:3.2.8'
    to_port = from_port = 6379
    image_options = BaseImage.image_options.copy()
    image_options.update(dict(
        cap_add=['IPC_LOCK'],
        mem_limit='200m'
    ))

    def check(self, host):
        sleep(1)
        return True


redis_image = Redis()
