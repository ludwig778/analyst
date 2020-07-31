import logging
import re

from collections import defaultdict

from bs4 import BeautifulSoup
from requests import Session

from analyst.settings import SCRAPPER_CONFIG

logger = logging.getLogger(__name__)


class CouldNotFindTicker(Exception):
    pass


class NoTickerDataFound(Exception):
    pass


class InvestingAdapter(object):

    def __init__(self, url=None):
        self.url = url
        self.config = SCRAPPER_CONFIG
        self.session = Session()
        self.session.headers["User-Agent"] = "Mozilla/5.0"

    def get_full_url(self, url):
        return self.url + url

    def get_soup(self, url):
        data = self.session.get(self.get_full_url(url))
        logger.critical(data.url)
        return BeautifulSoup(data.content, "html.parser")

    @staticmethod
    def check_filter(data, condition):
        return [data.get(arg) in values for arg, values in condition.items() if values]

    def parse_tr(self, tr_item, filter_key=None):
        tds = tr_item.findAll("td")
        country = tds[0].span.attrs["title"]
        link = tds[1].a.attrs["href"]
        name = tds[1].a.text.replace(";", "")

        datas = {"name": name,
                 "link": link,
                 "country": country}

        if filter_key:
            filter_dict = self.config.get(filter_key, {})
            include = filter_dict.get("include", {})
            exclude = filter_dict.get("exclude", {})

            if exclude != {} and any(self.check_filter(datas, exclude)):
                return {}
            elif include != {} and any(self.check_filter(datas, include)):
                return datas
            elif include == {} and exclude == {}:
                return datas
            return {}

        return datas

    def get_indices(self):
        datas = defaultdict(list)
        list_data = []
        soup = self.get_soup("/indices/major-indices")
        for tr_item in soup.find(id="cross_rates_container").findAll("tr")[1:]:
            tds = self.parse_tr(tr_item, filter_key="indice")
            if tds:
                datas[tds.get("country")].append(tds)

        for _country, indice_set in datas.items():
            list_data.append(indice_set)

        return datas.items()

    def get_assets(self, indice_url, page_indicator=""):
        assets = []
        soup = self.get_soup(
            indice_url + "-components" + page_indicator
        )

        for tr_item in soup.find(id="marketInnerContent").findAll("tr")[1:]:
            tds = self.parse_tr(tr_item, filter_key="asset")
            if tds:
                assets.append(tds)

        if not page_indicator:
            pagination = soup.find(id="paginationWrap")
            if pagination:
                page_nums = pagination.findAll("a", attrs={"class": "pagination"})
                for page_num in range(2, len(page_nums) + 1):
                    assets.extend(
                        self.get_assets(
                            indice_url,
                            page_indicator=f"/{page_num}"
                        )
                    )

        return assets

    @staticmethod
    def float_parsing(string):
        return float(string.replace(",", "").replace(" ", ""))

    @staticmethod
    def integer_parsing(string):
        return int(string.replace(",", "").replace(" ", ""))

    @staticmethod
    def first_element(elements):
        return float(elements.split()[0])

    @staticmethod
    def capital_parsing(cap):
        cap_dict = {"K": 3, "M": 6, "B": 9, "T": 12}
        number, prefix = cap[0:-1], cap[-1]
        return int(float(number)) * (10 ** cap_dict[prefix])

    @staticmethod
    def parse_extra_list(soup, parsing_dict):
        extra_dict = {}
        extra_list = soup.find("div", attrs={"class": "overviewDataTable"})

        if not extra_list:
            return {}

        for div in extra_list.findAll("div"):
            spans = div.findAll("span")
            key = spans[0].text
            value = spans[1].text
            parsing_conf = parsing_dict.get(key, None)
            if parsing_conf:
                if "n/a" in value.lower():
                    extra_dict[parsing_conf["replace"]] = parsing_conf["default"]
                else:
                    extra_dict[parsing_conf["replace"]] = parsing_conf["func"](value)

        return extra_dict

    @staticmethod
    def get_ticker_datas(soup, asset_url):
        ticker = None

        ticker_list = soup.find(id="DropdownSiblingsTable")
        if ticker_list:
            for tr_item in ticker_list.findAll("tr")[1:]:
                tds = tr_item.findAll("td")
                ticker = tds[1].a.text
                currency = tds[3].text

                if ticker.isdigit():
                    continue

                return {"pending_ticker": ticker,
                        "currency": currency}
        else:
            instrument = soup.findAll(
                "div",
                attrs={"class": "instrumentHead"}
            )
            if instrument:
                indice_text = instrument[0].h1.text
                splitted = re.split(r"\(|\)", indice_text)
                if len(splitted) > 1:
                    ticker = splitted[-2]
                else:
                    ticker = indice_text.split()[0]

        return {"pending_ticker": ticker}

    def get_asset_datas(self, asset_url):

        parsing_dict = {
            "Dividend (Yield)": {
                "replace": "dividend",
                "func": self.first_element,
                "default": 0.0
            },
            # ERROR ON INVESTING SITE WITH
            # BETA AND EPS SAME AS MARKET CAP
            # "Beta": {"replace": "beta", "func": float_parsing, "default": 0.0},
            # "EPS": {"replace": "eps", "func": float_parsing, "default": 0.0},
            "Shares Outstanding": {
                "replace": "shares",
                "func": self.integer_parsing,
                "default": 0
            },
            "Market Cap": {
                "replace": "cap",
                "func": self.capital_parsing,
                "default": 0
            },
            "Prev. Close": {
                "replace": "close",
                "func": self.float_parsing,
                "default": 0.0
            }
        }

        soup = self.get_soup(asset_url)
        ticker_data = self.get_ticker_datas(soup, asset_url)

        if "indices" in asset_url:
            kind = "I"
            if "pending_ticker" in ticker_data:
                ticker_data["pending_ticker"] = "^" + ticker_data["pending_ticker"]
        elif "currencies" in asset_url:
            kind = "F"
        elif "equities" in asset_url:
            kind = "S"
        else:
            raise NotImplementedError("For url: %s" % asset_url)

        extra_data = self.parse_extra_list(soup, parsing_dict)

        result = {"link": asset_url, "kind": kind}

        result["extra_data"] = {}

        if ticker_data:
            result["extra_data"].update(ticker_data)

        if extra_data:
            result["extra_data"].update(extra_data)

        return result
