import logging

from redis import Redis

logger = logging.getLogger(__name__)


class RedisAdapter(Redis):
    def __init__(self, prefix="", **kwargs):
        super().__init__(**kwargs)
        self.prefix = prefix

    @property
    def redis_prefix(self):
        return "/{}/".format(
            self.prefix
        )

    def invalidate_key(self, key):
        return self.delete(key)

    def set_key(self, key, value, **kwargs):
        return self.set(
            key,
            value,
            **kwargs
        )

    def get_key(self, key):
        return self.get(key)

    def get_keys(self, pattern="*"):
        return self.keys(pattern)

    def remove_redis_prefix(self, data, redis_prefix=None):
        if not redis_prefix:
            redis_prefix = self.redis_prefix
        return {
            item[0].replace(redis_prefix, ''): item[1]
            for item in data.items()
        }

    def get_cached_data(self, pattern="*"):
        keys = self.get_keys(pattern)
        if keys:
            return self.remove_redis_prefix(
                self.get_many(keys)
            )
        return []

    def keys(self, pattern='*'):
        return super().keys("/{}/{}".format(self.__class__.__name__.lower(), pattern))
