try:
    from guillotina.async_util import IAsyncUtility
except ImportError:
    from guillotina.async import IAsyncUtility


CACHE_PREFIX = 'gcache2-'

class IRedisChannelUtility(IAsyncUtility):
    pass


class IRedisUtility(IAsyncUtility):
    pass
