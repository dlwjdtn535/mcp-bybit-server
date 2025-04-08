from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

candle_cache = CacheManager(**parse_cache_config_options({
    'cache.type': 'file',
    'cache.data_dir': '/tmp/cache/data',
    'cache.lock_dir': '/tmp/cache/lock',
}))