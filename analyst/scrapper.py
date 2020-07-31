import logging

from adapters import investing
from analyst.models import Asset, Index
from analyst.utils import fill_cache

logger = logging.getLogger(__name__)


class ScrapManager(object):

    def setup(self):
        self.asset_cache = {}
        self.asset_index_cache = {}

        fill_cache(self.asset_cache, Asset.objects.all(), key="name")
        fill_cache(self.asset_index_cache, Index.objects.all(), key="name")

    def get_or_create_asset(self, asset=None, name=None, kind=None, link=None, country=None, extra_data=None, **data):
        asset = asset or self.asset_cache.get(name, None)
        action = None

        if not asset:
            logger.info(f"Creating asset {name}")
            asset = Asset.objects.create(
                name=name,
                kind=kind,
                country=country,
                link=link,
                extra_data=extra_data
            )
            action = "created"
        else:
            to_update = False
            logger.info(f"Updated asset {name}")

            if country and asset.country != country:
                asset.country = country
                to_update = True

            if link and asset.link != link:
                asset.link = link
                to_update = True

            if kind and asset.kind != kind:
                asset.kind = kind
                to_update = True

            if extra_data and asset.extra_data != extra_data:
                asset.extra_data = extra_data
                to_update = True

            if to_update:
                asset.save()

                action = "updated"

        return action, asset

    def get_or_create_index(self, index=None, name=None, link=None, country=None, extra_data=None, **data):
        index = index or self.asset_index_cache.get(name, None)
        action = None

        if not index:
            logger.info(f"Creating index {name}")
            index = Index.objects.create(name=name, link=link, country=country)
            action = "created"

        elif index.link != link or index.country != country:
            logger.info(f"Updating index {name}")
            index.country = country
            index.link = link

            index.save()
            action = "updated"

        return action, index

    def update_indexes(self):
        logger.info("Launching Indexes scrapping")
        self.setup()

        results = []

        for country, indexes in investing.get_indices():
            for index_data in indexes:
                action, index = self.get_or_create_index(**index_data)

                index_data["action"] = action

                results.append((index, action))

        logger.info("End of scrapping")
        return results

    def update_index(self, index):
        logger.info("Launching Index scrapping")
        self.setup()

        index_data = investing.get_asset_datas(index.link)

        action, index_asset = self.get_or_create_asset(name=index.name, **index_data)

        if index.indice != index_asset:
            index.indice = index_asset
            index.save()

        return index_asset, action

    def update_assets(self, index):
        logger.info("Launching Index scrapping")
        self.setup()

        index_assets = list(index.assets.all())

        results = []
        temp_results = {}
        list_assets = []

        for asset_data in investing.get_assets(index.link):
            logger.warning(asset_data)

            action, asset = self.get_or_create_asset(**asset_data)
            list_assets.append(asset)

            temp_results[asset] = action

        for asset in index_assets:
            if asset not in list_assets:
                index.assets.remove(asset)
                logger.info(f"Removing from index {index.name} the asset {asset.name}")

                results.append((asset, temp_results.get(asset, None), "removed"))
            else:
                results.append((asset, temp_results.get(asset, None), None))

        for asset in list_assets:
            if asset not in index_assets:
                index.assets.add(asset)
                logger.info(f"Adding to index {index.name} the asset {asset.name}")

                results.append((asset, temp_results.get(asset, None), "added"))

        index.save()

        logger.info("End of scrapping")

        return results

    def update_asset(self, asset):
        logger.info("Launching Asset scrapping")

        asset_data = investing.get_asset_datas(asset.link)

        action, asset = self.get_or_create_asset(asset=asset, **asset_data)

        return asset, action


scrap_manager = ScrapManager()
