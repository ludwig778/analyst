import logging

from django.contrib.auth.models import Group, User
from rest_framework import serializers
from rest_framework.reverse import reverse

from analyst.models import Asset, Index, Portfolio

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class AssetListSerializer(serializers.RelatedField):
    def to_representation(self, obj):
        return reverse(
            'asset-detail',
            args=[obj.id],
            request=self.context.get("request")
        )


class IndexListSerializer(serializers.RelatedField):
    def to_representation(self, obj):
        return reverse(
            'index-detail',
            args=[obj.id],
            request=self.context.get("request")
        )


class PortfolioListSerializer(serializers.RelatedField):
    def to_representation(self, obj):
        return reverse(
            'portfolio-detail',
            args=[obj.id],
            request=self.context.get("request")
        )


class AssetSerializer(serializers.ModelSerializer):
    kind = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = ('id', 'url', 'name', 'kind', 'ticker', 'link', 'country', 'last_close', 'dividend')

    def get_kind(self, obj):
        return obj.kind_expanded


class AssetDetailSerializer(serializers.ModelSerializer):
    indexes = IndexListSerializer(many=True, read_only=True)
    kind = serializers.SerializerMethodField()
    datas = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Asset
        fields = ('id', 'name', 'url', 'kind', 'ticker', 'indexes', 'datas', 'link', 'country', 'last_close', 'dividend')
        read_only_fields = ('ticker',)
        search_fields = ['ticker']

    def get_datas(self, obj):
        return {
            df_name: {k.strftime("%s"): v for k, v in df.items()}
            for df_name, df in obj.get_df().items()
        }

    def get_kind(self, obj):
        return obj.kind_expanded


class IndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = Index
        fields = ('id', 'url', 'name', 'link', 'country')


class IndexDetailSerializer(serializers.ModelSerializer):
    indice = AssetListSerializer(many=False, read_only=True)
    assets = AssetListSerializer(many=True, read_only=True)
    datas = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Index
        fields = ('id', 'url', 'name', 'indice', 'datas', 'assets', 'link')

    def get_datas(self, obj):
        return {
            df_name: {k.strftime("%s"): v for k, v in df.items()}
            for df_name, df in obj.get_df().items()
        }


class PortfolioSerializer(serializers.ModelSerializer):
    assets = AssetListSerializer(many=True, read_only=True)

    class Meta:
        model = Portfolio
        fields = ('id', 'url', 'name', 'assets', 'weights')
