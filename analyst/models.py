import logging

import pandas as pd

from django.contrib.postgres.fields import JSONField
from django.db import models

from adapters import alpha_vantage, influxdb
from analyst.utils import (check_close_price, get_offset_date,
                           is_dataframe_outdated)

DEFAULT_DF = ["close"]

logger = logging.getLogger(__name__)


class AssetManager(models.QuerySet):
    def get_indices(self):
        return self.filter(kind='I')

    def exclude_indices(self):
        return self.exclude(kind='I')

    def get_stocks(self):
        return self.filter(kind='S')

    def get_forex(self):
        return self.filter(kind='F')

    # def get_cryptos(self):
    #     return self.filter(kind='C')


class DataFrameManager(object):
    @staticmethod
    def _get_dataframe(assets, **kwargs):
        if "fields" not in kwargs:
            kwargs.update({"fields": "close"})

        df = pd.DataFrame()

        for asset in assets:
            asset_df = asset.get_df(**kwargs)
            if asset_df is not None:
                asset_df.columns = [asset.analysis_name]
                df = df.join(asset_df, how="outer")

        return df.asfreq('d')

    def get_assets_dataframe(self, **kwargs):
        return self._get_dataframe(
            self.assets.all(),
            **kwargs
        )

    def get_indices_dataframe(self, **kwargs):
        return self._get_dataframe(
            self.get_indices(),
            **kwargs
        )


class Asset(models.Model):

    class Meta:
        ordering = ['id']

    ASSET_TYPE = (
        ('I', 'Indice'),
        ('S', 'Stock'),
        ('F', 'Forex'),
        ('C', 'Crypto-currency')
    )
    ASSET_TYPE_DICT = dict(ASSET_TYPE)

    name = models.CharField(max_length=30, unique=True)
    kind = models.CharField(max_length=1, choices=ASSET_TYPE, null=True)
    ticker = models.CharField(max_length=30, null=True)
    description = models.CharField(max_length=60, null=True)

    link = models.CharField(max_length=64, null=True)
    country = models.CharField(max_length=64, null=True)
    objects = AssetManager().as_manager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    extra_data = JSONField(null=True, default=dict)

    @property
    def analysis_name(self):
        return "{}:{}".format(
            self.id,
            self.ticker
        )

    @property
    def influx_name(self):
        return "asset_{}".format(self.id)

    def get_df(self, **kwargs):
        df = influxdb.get(
            self.influx_name,
            **kwargs
        )
        if df:
            return df.get(self.influx_name)

        return {}

    def store_df(self, df, **kwargs):
        return influxdb.store(self.influx_name, df, **kwargs)

    def get_latest_measure(self):
        return self.get_df(extra_query="GROUP BY * ORDER BY DESC LIMIT 1")

    def __str__(self):
        return self.name

    @property
    def kind_expanded(self):
        return self.ASSET_TYPE_DICT.get(self.kind)

    @property
    def indexes(self):
        return self.index_set.all()

    @property
    def portfolios(self):
        return self.portfolio_set.all()

    @property
    def pending_ticker(self):
        return self.extra_data.get("pending_ticker")

    @property
    def currency(self):
        return self.extra_data.get("currency")

    @property
    def last_close(self):
        return self.extra_data.get("close")

    @property
    def dividend(self):
        return self.extra_data.get("dividend")

    def update_dataframe(self, set_ticker=None, full=False):
        ticker = set_ticker or self.ticker

        if not is_dataframe_outdated(
            self.get_latest_measure(),
            get_offset_date()
        ):
            logger.debug("Asset is up-to-date")
            return True

        if self.kind in ("S", "F", "I"):
            datas = alpha_vantage.get(ticker, full=full, asset_type=self.kind)
        else:
            raise NotImplementedError("May be implemented soon for cryptocurrency")

        if not check_close_price(datas, self.last_close):
            return False

        self.store_df(datas)
        logger.debug(f"Asset value saved : {ticker}")

        return datas


class Index(models.Model, DataFrameManager):

    class Meta:
        ordering = ['id']

    name = models.CharField(max_length=30, unique=True)
    indice = models.OneToOneField(
        Asset,
        on_delete=models.DO_NOTHING,
        related_name="indice",
        null=True
    )
    assets = models.ManyToManyField(Asset)
    link = models.CharField(max_length=64, null=True)
    country = models.CharField(max_length=64, null=True)

    def __str__(self):
        return self.name

    def get_df(self, **kwargs):
        if self.indice:
            df = influxdb.get(
                self.indice.influx_name,
                **kwargs
            )
            if df:
                return df.get(self.indice.influx_name)

        return {}

    def get_assets_df(self, **kwargs):
        assets_df = pd.DataFrame()

        for asset in self.assets.all():
            df = influxdb.get(
                asset.influx_name,
                **kwargs
            )
            df = df[asset.influx_name]
            df.columns = [asset.analysis_name]

            if isinstance(df, pd.DataFrame) and not df.empty:
                if assets_df.empty:
                    assets_df = df
                else:
                    assets_df = assets_df.join(df)

        return assets_df

    def get_indices(self):
        return [self.indice]


class Portfolio(models.Model, DataFrameManager):

    class Meta:
        ordering = ['id']

    name = models.CharField(max_length=30, unique=True)
    assets = models.ManyToManyField(Asset)
    indices = JSONField(null=True, default=dict)
    weights = JSONField(null=True, default=dict)

    def __str__(self):
        return self.name

    def get_indices(self):
        return [
            Asset.objects.get(id=value_id)
            for value_id in set(self.indices.values())
        ]

    def normalize_weights(self):
        normalized = {}
        total_weight = sum(self.weights.values())
        for asset in self.assets.all():
            normalized[asset.id] = float(self.weight.get(asset.id)) / total_weight

        return normalized
