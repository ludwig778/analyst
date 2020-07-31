import logging

from datetime import datetime
from time import sleep

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class AlphaVantageException(Exception):
    pass


class SymbolNotFound(AlphaVantageException):
    pass


class TooMuchApiCall(AlphaVantageException):
    pass


class NoDataAvailable(AlphaVantageException):
    pass


class AlphaVantageAdapter(object):
    def __init__(self, url=None, key=None):
        self.url = url
        self.key = key
        self.session = requests.Session()
        self.last_call = datetime.now()

    def _wait_before_call(self):
        """
        To avoid reaching the api call limit
        for there are only 5 requests allowed by minutes
        """
        now = datetime.now()
        delta = (now - self.last_call).seconds

        if delta < 12:
            sleep(12 - delta)

        self.last_call = datetime.now()

    def _build_dataframe(self, data):
        """
        Build a generic dataframe with a daily datetime index
        with float values
        """
        df = pd.DataFrame(data).T
        df.index = pd.to_datetime(df.index)

        df = df[["4. close"]]
        df.sort_index(inplace=True)

        return df.applymap(lambda v: float(v))

    def _build_url_query(self, symbol, asset_type, freq="DAILY", full=False, interval="60min"):
        """
        Build url query to hit the specified symbol resource
        """
        output_size = 'full' if full else 'compact'

        if asset_type == "F":
            from_symbol, to_symbol = symbol.split("/")
            url_query = (f"{self.url}/query?function=FX_{freq}&from_symbol={from_symbol}&"
                         f"to_symbol={to_symbol}&outputsize={output_size}&apikey={self.key}")
        elif asset_type in ("S", "I"):
            url_query = (f"{self.url}/query?function=TIME_SERIES_{freq}&symbol={symbol}&"
                         f"outputsize={output_size}&apikey={self.key}")

        if freq == "INTRADAY":
            url_query += f"&interval={interval}"

        return url_query

    def get(self, symbol, asset_type=None, **kwargs):
        """
        Get the latest close data for the specified symbol
        """
        if not asset_type:
            logger.error("No asset_type argument set")
            raise Exception("asset_type must be set")

        url_query = self._build_url_query(symbol, asset_type, **kwargs)

        self._wait_before_call()

        ret = self.session.get(url_query)

        if not ret.ok:
            logger.error(f"No data available for {symbol} ({ret.reason})")
            raise NoDataAvailable(symbol)

        ret_json = ret.json()

        if ret_json.get("Error Message"):
            logger.error(f"Symbol {symbol} not found")
            raise SymbolNotFound(symbol)

        elif ret_json.get("Note"):
            logger.error("Too much api calls")
            raise TooMuchApiCall(symbol)

        if asset_type == "F":
            data = ret_json.get("Time Series FX (Daily)")
        elif asset_type in ("S", "I"):
            data = ret_json.get("Time Series (Daily)")

        if data:
            return self._build_dataframe(data)
        else:
            logger.error(f"No data available for {symbol}")
            raise NoDataAvailable(symbol)
