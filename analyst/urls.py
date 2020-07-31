from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from analyst.views import (AssetViewSet, GroupViewSet, IndexViewSet,
                           PortfolioViewSet, UserViewSet)

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'assets', AssetViewSet)
router.register(r'indexes', IndexViewSet)
router.register(r'portfolios', PortfolioViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        path('__debug__/', include(debug_toolbar.urls))
    )
