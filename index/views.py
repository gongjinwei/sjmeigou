from rest_framework.viewsets import ModelViewSet
from rest_framework.views import Response, status
from rest_framework.decorators import action

from django.db.models import Count
import datetime

from tools.viewset import ListOnlyViewSet, CreateListViewSet

from . import models, serializers
from goods.serializers import FirstClassSerializer
from goods.models import FirstClass
from platforms.models import DeliverAdcode
from tools.contrib import look_up_adocode
# Create your views here.

from store.models import StoreFavorites, GoodFavorites
from order.models import StoreOrder
from store.serializers import HistoryDeleteSerializer


class BannerView(ModelViewSet):
    serializer_class = serializers.BannerSerializer
    queryset = models.Banner.objects.all()

    def perform_create(self, serializer):
        serializer.save(last_operator=self.request.user)


class UmViewSets(ListOnlyViewSet):

    def list(self, request, *args, **kwargs):
        result = {
            "banners": serializers.BannerSerializer(models.Banner.objects.all(), many=True).data,
            "sorts": FirstClassSerializer(FirstClass.objects.all(), many=True).data,
        }
        return Response(result)


class RecruitView(ModelViewSet):
    serializer_class = serializers.RecruitSerializer
    queryset = models.RecruitMerchant.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data.update(last_operator=self.request.user)
        image, created = self.queryset.update_or_create(defaults=serializer.validated_data, name='propagate')
        return Response(image.image.url)


class ApplicationViewSets(ModelViewSet):
    serializer_class = serializers.ApplicationSerializer
    queryset = models.Application.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if models.Application.objects.filter(application_user=self.request.user).exists():
            return Response({'code': 2001, 'msg': '你的信息已提交，请不要重复申请'})
        self.perform_create(serializer)
        return Response({'code': 1000, 'msg': '申请成功'})

    def perform_create(self, serializer):
        latitude = serializer.validated_data['latitude'],
        longitude = serializer.validated_data['longitude'],
        adocode = look_up_adocode('%6f,%6f' % (longitude, latitude))
        if adocode and DeliverAdcode.objects.filter(code=adocode).exists():
            serializer.save(application_user=self.request.user, adocode=adocode)
        else:
            Response({'code': 2002, 'msg': '你所处的区域不在配送范围'})

    def get_queryset(self):

        if self.request.user.is_staff:
            return models.Application.objects.all()
        elif self.request.user.is_authenticated:
            return models.Application.objects.filter(application_user=self.request.user)

        return models.Application.objects.none()


class MessageOfMineView(ListOnlyViewSet):
    def list(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'data': None})
        else:
            data = {}
            data.update(GoodFavorites.objects.filter(user=request.user).aggregate(good_favorites_num=Count('good')))
            data.update(StoreFavorites.objects.filter(user=request.user).aggregate(store_favorites_num=Count('store')))
            data.update(models.GoodTrack.objects.filter(user=request.user).aggregate(good_tracks_num=Count('good')))
            data.update({'orders': StoreOrder.objects.filter(user=request.user, state__in=[1, 2, 3, 4, 7]).values(
                'state', state_num=Count('store_order_no'))})
            return Response({'data': data})


this_month = datetime.datetime.now().month
last_month = this_month-1 if this_month-1>0 else this_month+11


class GoodTrackViewSets(CreateListViewSet):
    queryset = models.GoodTrack.objects.filter(visible=True,date__month__in=[this_month,last_month])
    serializer_class = serializers.GoodTrackSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = self.queryset
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
        else:
            return queryset.none()

    @action(methods=['post'], detail=True, serializer_class=HistoryDeleteSerializer)
    def bulk_delete(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data['ids']
        user_ids = list(self.queryset.filter(user=request.user).values_list('id', flat=True))
        if set(ids).issubset(user_ids):
            self.queryset.filter(id__in=ids).update(visible=False)
            return Response({'code': 1000, 'msg': '删除成功'})
        else:
            return Response({'code': 4150, 'msg': '删除错误'})
