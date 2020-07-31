import logging

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from os import environ

import pytz

from pandas import DataFrame

logger = logging.getLogger(__name__)


def get_tz_datetime(timedelta):
    now = datetime.now().replace(tzinfo=pytz.utc)
    return now - timedelta


def is_dataframe_outdated(df, limit):
    return not (
        isinstance(df, DataFrame) and
        not df.empty and
        df.iloc[-1].name > limit
    )


def check_close_price(df, price, diff_percentage=0.75):
    last_df_close = df.iloc[-1]["close"]
    return (
        last_df_close < price / diff_percentage and
        last_df_close > price * diff_percentage
    )


def get_offset_date():
    return (
        get_tz_datetime(timedelta(days=1 + max(0, date.today().weekday() - 3)))
        .replace(hour=0, minute=0, second=0, microsecond=0)
    )


def is_crypto(ticker):
    major_currencies = ("BTC", "ETH")
    if "/" in ticker:
        ticker_split = ticker.split("/")
        return any(c in ticker_split for c in major_currencies)
    return False


def is_forex(ticker):
    major_currencies = ("EUR", "USD", "GBP", "JPY", "CHF", "AUD")
    if "/" in ticker:
        ticker_split = ticker.split("/")
        return any(c in ticker_split for c in major_currencies)
    return False


def fill_cache(cache, queryset, key="pk", bidirect=False):
    for item in queryset:
        cache[getattr(item, key)] = item
    if bidirect:
        for item in queryset:
            cache[item] = getattr(item, key)


def threaded(func, items, *args, workers=10, condition=None, **kwargs):
    results = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                func,
                key,
                values,
                *args,
                **kwargs
            ): key
            for key, values in items
            if (
                not condition or
                callable(condition) and condition(key, values) is True
            )
        }
        for future in as_completed(futures):
            results.update({
                futures[future]:
                future.result()
            })
        return results


def join_dicts(dict1, dict2):
    return {**dict2, **dict1}


def get_timestamp(timestamp):
    return timestamp.strftime("%s") if isinstance(timestamp, datetime) else timestamp


def get_config_from_env(prefix):
    config = {}

    for key, value in environ.items():
        if key.startswith(f"{prefix}_"):
            key = key.replace(f"{prefix}_", "").lower()
            config[key] = value

    return config


def get_dict_config_from_env(prefix, dataclass=None):
    config = defaultdict(dict)

    for key, value in environ.items():
        if key.startswith(f"{prefix}_"):
            _, sub_key, key = key.split("_", 2)

            if value.lower() in ["false", "true"]:
                value = eval(value.capitalize())

            config[sub_key.lower()].update({key.lower(): value})

    if dataclass:
        for key in config.keys():
            config[key] = dataclass(key=key, **config[key])

    return config
