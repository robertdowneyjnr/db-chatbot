# redis_connection.py
import redis


class RedisConnection:
    _instance = None

    @staticmethod
    def get_instance(host, port, password):
        if RedisConnection._instance is None:
            url = f"rediss://{host}:{port}"
            RedisConnection._instance = redis.from_url(url, password=password)
        return RedisConnection._instance

    @staticmethod
    def get_url(host, port, password):
        return f"rediss://:{password}@{host}:{port}"
