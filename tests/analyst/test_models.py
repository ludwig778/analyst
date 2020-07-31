from pytest import mark


@mark.database
def test_assetmanager(models_object):
    asset_obj = models_object.Asset.objects

    def check_kind(objects, kind, compare):
        assert all([
            getattr(obj.kind, "__{}__".format(compare))(kind)
            for obj in objects
        ])

    for assets, kind, compare in (
        (asset_obj.get_indices(), "I", "eq"),
        (asset_obj.exclude_indices(), "I", "ne"),
        (asset_obj.get_stocks(), "S", "eq"),
        (asset_obj.get_forex(), "F", "eq"),
    ):
        check_kind(assets, kind, compare)
