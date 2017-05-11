Introduction
============

`guillotina_rediscache` implements redis into guillotina with an additional
in-memory layer cache.

In order to coordinate invalidating the in-memory cache, `guillotina_rediscache`
utilizes the pub/sub feature redis provides.



Configuration
-------------

app_settings for this::

    {
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


TODO
----

- pub/sub
- tests
- stats
- api endpoint to...
  - inspect, get stats
  - clear
