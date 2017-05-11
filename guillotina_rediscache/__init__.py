from guillotina import configure


app_settings = {
    "redis": {
        'host': 'localhost',
        'port': 6379,
        'ttl': 3600,
        'memory_cache_size': 1000,
        'pool': {
            'minsize': 5,
            'maxsize': 100
        }
    }
}


def includeme(root, settings):
    configure.scan('guillotina_rediscache.cache_strategy')
