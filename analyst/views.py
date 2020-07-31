import logging

from django.contrib.auth.models import Group, User
from pandas import DataFrame
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from adapters.alpha_vantage import SymbolNotFound
from analyst.models import Asset, Index, Portfolio
from analyst.scrapper import scrap_manager
from analyst.serializers import (AssetDetailSerializer, AssetSerializer,
                                 GroupSerializer, IndexDetailSerializer,
                                 IndexSerializer, PortfolioSerializer,
                                 UserSerializer)

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    filterset_fields = search_fields = ('id', 'name', 'kind', 'ticker')
    ordering_fields = ('id', 'name', 'kind', 'created_at', 'updated_at')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AssetDetailSerializer
        return AssetSerializer

    @action(detail=True)
    def fetch(self, request, *args, **kwargs):
        if not (asset := self.get_object()):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        asset, action = scrap_manager.update_asset(asset)

        if not request.GET.get("scrap_only"):
            try:
                asset.update_dataframe(full=True)
            except SymbolNotFound:
                pass

        return Response({
            "action": action,
            **AssetSerializer(asset, context={"request": request}).data
        })

    @action(detail=True)
    def update_dataframe(self, request, *args, **kwargs):
        if not (asset := self.get_object()):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        asset.update_dataframe(full=True)

        return Response({"success": True})

    @action(detail=True, methods=["GET", "POST"])
    def set_ticker(self, request, *args, **kwargs):
        if not (asset := self.get_object()):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if not (ticker := request.data.get("ticker", asset.ticker or asset.pending_ticker)):
            return Response({
                "detail": "No ticker found in POST data and extra_data."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = asset.update_dataframe(set_ticker=ticker, full=True)
        except SymbolNotFound:
            return Response({
                "defail": "Symbol provided not found"
            }, status=status.HTTP_404_NOT_FOUND)

        if isinstance(result, DataFrame):
            asset.ticker = ticker
            asset.save()

            return Response({"success": True})

        elif result is True:
            return Response({"defail": "Asset dataframe is already up-to-date"})

        else:
            return Response({
                "detail": "Could not found data with this ticker"
            }, status=status.HTTP_400_BAD_REQUEST)


class IndexViewSet(viewsets.ModelViewSet):
    queryset = Index.objects.all()
    serializer_class = IndexSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return IndexDetailSerializer
        return IndexSerializer

    @action(detail=False)
    def fetch_all(self, request, *args, **kwargs):
        return Response([
            {
                "action": action,
                **IndexSerializer(index, context={"request": request}).data
            }
            for index, action in scrap_manager.update_indexes()
        ])

    @action(detail=True)
    def fetch(self, request, *args, **kwargs):
        if not (index := self.get_object()):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        result = {}

        index_asset, action = scrap_manager.update_index(index)
        result["indice"] = {
            "action": action,
            **AssetSerializer(index_asset, context={"request": request}).data
        }

        result["assets"] = [
            {
                "action": action,
                "from_index": from_index,
                **AssetSerializer(asset, context={"request": request}).data
            }
            for asset, action, from_index in scrap_manager.update_assets(index)
        ]

        return Response(result)

    @action(detail=True)
    def assets(self, request, *args, **kwargs):
        if not (index := self.get_object()):
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response([AssetSerializer(asset, context={"request": request}).data for asset in index.assets.all()])


class PortfolioViewSet(viewsets.ModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
