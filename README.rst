Introduction
============

.. image:: https://travis-ci.org/guillotinaweb/guillotina_rediscache.svg?branch=master
   :target: https://travis-ci.org/guillotinaweb/guillotina_rediscache


`guillotina_rediscache` implements redis into guillotina with an additional
in-memory layer cache.

In order to coordinate invalidating the in-memory cache, `guillotina_rediscache`
utilizes the pub/sub feature redis provides.



Configuration
-------------

app_settings for this::

    {
      "databases": {
        "db": {
          ...
          "cache_strategy": "redis"
          ...
        }
      },
      "redis": {
          'host': 'localhost',
          'port': 6379,
          'ttl': 3600,
          'memory_cache_size': 209715200,
          'pool': {
              'minsize': 5,
              'maxsize': 100
          }
      }
    }



Run measures
------------

Using guillotina run command::

    ./bin/g run --script=measures/serialize.py -c measures/config.yaml


With profiling::

    ./bin/g run --script=measures/serialize.py -c measures/config.yaml --line-profiler --line-profiler-matcher="*serialize*"
