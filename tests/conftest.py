import json

from os import path

import pandas as pd

from pytest import fixture

from analyst.models import Asset, Index, Portfolio
from analyst.settings import FIXTURE_PATH


class AnalysisTestDatas(object):
    def __init__(self, path):
        datas = self._get_datas(path)

        for model, label in (
            (Asset, "assets"),
            (Index, "indexes"),
            (Portfolio, "portfolios"),
        ):
            setattr(self, model.__name__, model)
            setattr(self, label, dict())

            for obj in datas.get(label):
                getattr(
                    self,
                    "_update_{}".format(label)
                )(obj)

    def _get_datas(self, path):
        with open(path) as fd:
            return json.loads(fd.read())

    @staticmethod
    def to_dataframe(datas):
        df = pd.DataFrame(datas, columns=("timestamp", "close"))
        df.index = pd.to_datetime(df.timestamp, unit="s")
        return df[["close"]]

    def _update_assets(self, asset_data):
        df_data = asset_data.pop("datas")
        asset = Asset.objects.create(**asset_data)

        asset.store_df(
            self.to_dataframe(df_data),
            reset=True
        )

        self.assets.update({asset.id: asset})

    def _update_indexes(self, index_data):
        index_id = index_data.get("id")

        indice = self.assets.get(index_data.get("indice"))
        assets = [self.assets.get(asset_id) for asset_id in index_data.get("assets")]

        index = Index.objects.create(
            id=index_id,
            name=index_data.get("name"),
            indice=indice
        )
        index.assets.set(assets)
        index.save()

        self.indexes.update({index_id: index})

    def _update_portfolios(self, portfolio_data):
        portfolio_id = portfolio_data.get("id")

        portfolio = Portfolio.objects.create(
            id=portfolio_id,
            name=portfolio_data.get("name")
        )

        portfolio.assets.set([
            self.assets.get(asset_id) for asset_id in portfolio_data.get("assets")
        ])

        portfolio.indices = {int(k): v for k, v in portfolio_data.get("indices").items()}
        portfolio.weights = {int(k): v for k, v in portfolio_data.get("weights").items()}
        portfolio.save()

        self.portfolios.update({portfolio_id: portfolio})


@fixture(scope="module", autouse=True)
def models_object(django_db_blocker):
    with django_db_blocker.unblock():

        for model in (
            Portfolio,
            Index,
            Asset
        ):
            for obj in model.objects.all():
                obj.delete()

        yield AnalysisTestDatas(
            path.join(
                FIXTURE_PATH,
                "base",
                "fixtures.json"
            )
        )
