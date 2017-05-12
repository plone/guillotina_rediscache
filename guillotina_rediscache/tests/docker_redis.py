from time import sleep


REDIS_IMAGE = 'redis:3.2.8'


def run_docker_redis(label='testingredis'):
    import docker
    docker_client = docker.from_env(version='1.23')

    # Clean up possible other docker containers
    test_containers = docker_client.containers.list(
        all=True,
        filters={'label': label})
    for test_container in test_containers:
        test_container.stop()
        test_container.remove(v=True, force=True)

    # Create a new one
    container = docker_client.containers.run(
        name='my-etcd-1',
        image=REDIS_IMAGE,
        labels=[label],
        detach=True,
        ports={
            '6379/tcp': 6379
        },
        cap_add=['IPC_LOCK'],
        mem_limit='200m'
    )
    ident = container.id
    count = 1

    opened = False
    host = ''

    print('starting redis')
    while count < 30 and not opened:
        count += 1
        try:
            docker_client.containers.get(ident)
        except docker.errors.NotFound:
            continue
        sleep(1)
    print('redis started')
    return host


def cleanup_redis_docker(label='testingredis'):
    import docker
    docker_client = docker.from_env(version='1.23')
    # Clean up possible other docker containers
    test_containers = docker_client.containers.list(
        all=True,
        filters={'label': label})
    for test_container in test_containers:
        test_container.kill()
        test_container.remove(v=True, force=True)
