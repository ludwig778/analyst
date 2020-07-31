from adapters.alpha_vantage import AlphaVantageAdapter
from adapters.influxdb import InfluxDBAdapter
from adapters.investing import InvestingAdapter
from adapters.redis import RedisAdapter
from analyst.settings import (ALPHA_VANTAGE_CONFIG, INFLUXDB_CONFIG,
                              INVESTING_CONFIG, REDIS_CONFIG)

alpha_vantage = AlphaVantageAdapter(**ALPHA_VANTAGE_CONFIG)
influxdb = InfluxDBAdapter(**INFLUXDB_CONFIG)
investing = InvestingAdapter(**INVESTING_CONFIG)
redis = RedisAdapter(**REDIS_CONFIG)
