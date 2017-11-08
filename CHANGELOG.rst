1.0.11 (2017-11-08)
-------------------

- Handle CancelledError
  [vangheem]


1.0.10 (2017-11-06)
-------------------

- upgrade for guillotina 2.0.0
  [vangheem]


1.0.9 (2017-10-23)
------------------

- Fix handling connection objects and releasing back to pool
  [vangheem]


1.0.8 (2017-10-23)
------------------

- Fix use of pool
  [vangheem]

1.0.7 (2017-10-23)
------------------

- Use pickle instead of json from load/dumps because it is much faster
  [vangheem]


1.0.6 (2017-10-19)
------------------

- Use ujson
  [vangheem]


1.0.5 (2017-10-02)
------------------

- Track all keys needing invalidation and do invalidation in an async task
  so the request can finish faster.
  [vangheem]


1.0.4 (2017-05-29)
------------------

- Test fixes
  [vangheem]


1.0.3 (2017-05-26)
------------------

- Fix delete not properly invalidating cache
  [vangheem]


1.0.2 (2017-05-15)
------------------

- Fix channel publishing invalidations
  [vangheem]


1.0.1 (2017-05-15)
------------------

- Fix release


1.0.0 (2017-05-15)
------------------

- initial release
