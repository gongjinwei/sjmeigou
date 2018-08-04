from rest_framework.views import Response, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser,AllowAny
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404

from django.conf import settings
from django.core.files.base import ContentFile
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet


from tools.viewset import CreateOnlyViewSet, ListDeleteViewSet, RetrieveUpdateViewSets,RetrieveOnlyViewSets,ListOnlyViewSet
from tools.permissions import MerchantOrReadOnlyPermission
from tools.contrib import look_up_adocode

from guardian.shortcuts import assign_perm


import requests, uuid


# Create your views here.

from . import serializers, models
from index.models import Application
from goods.models import GoodDetail,SearchHistory
from platforms.models import CodeWarehouse,Account,DeliverAdcode
from order.models import CommentContent

appid = getattr(settings, 'APPID')
secret = getattr(settings, 'APPSECRET')


class StoresViewSets(ModelViewSet):
    """
        用于查看自己的店铺，验证店铺激活码并创建一个店铺
    """
    serializer_class = serializers.StoresSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['active_code']
        application = serializer.validated_data['info']
        if application.application_status != 5:
            return Response('你的申请未通过,请通过后进行再验证', status=status.HTTP_400_BAD_REQUEST)
        if models.Stores.objects.filter(user=request.user,active_state=1).exists():
            return Response('你已经验证过了',status=status.HTTP_400_BAD_REQUEST)

        if CodeWarehouse.objects.filter(code=code, use_state=0).exists():

            # 默认填写店铺名，收获地址
            serializer.validated_data.update({
                "name":application.store_name,
                "receive_address":application.store_address,
                "longitude":application.longitude,
                "latitude":application.latitude,
                'adcode':application.adcode
            })
            self.perform_create(serializer)
            # 更新激活码状态
            application.codewarehouse.use_state = 1
            application.codewarehouse.active_user = request.user
            application.codewarehouse.save()
            Application.objects.filter(pk=application.pk).update(application_status=6)

            # 将申请用户加入权限组

            assign_perm('store.change_stores', request.user, request.user.stores)

            # 为店铺创建余额账号和物流账号
            Account.objects.create(store=request.user.stores,account_type=3)

            Account.objects.create(store=request.user.stores,account_type=5)

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response('激活码错误或已经使用过了', status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, active_state=1)

    def get_queryset(self):

        if self.request.user.is_staff:
            return models.Stores.objects.all()
        elif self.request.user.is_authenticated:
            return models.Stores.objects.filter(user=self.request.user)

        return models.Stores.objects.none()


class DepositView(ModelViewSet):
    """
        记录与发放保证金申请
    """
    serializer_class = serializers.DepositSerializer

    def get_queryset(self):

        if self.request.user.is_staff:
            return models.Deposit.objects.all()
        elif self.request.user.is_authenticated:
            return models.Deposit.objects.filter(application=self.request.user.application)

        return models.Deposit.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application_id = serializer.validated_data['application']
        if request.user.application.application_id == application_id:

            obj, created = models.Deposit.objects.get_or_create(defaults={'application': request.user.application},
                                                                application=request.user.application)

            return Response(serializers.DepositSerializer(instance=obj).data, status=status.HTTP_201_CREATED)
        else:
            return Response('您无此申请号', status=status.HTTP_400_BAD_REQUEST)


class StoreQRCodeViewSets(CreateOnlyViewSet):
    """
        用于店铺二维码图片的生成
    """
    serializer_class = serializers.StoreQRCodeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if models.StoreQRCode.objects.filter(**serializer.validated_data).exists():
            storeqrcode = models.StoreQRCode.objects.filter(**serializer.validated_data)[0]
            return Response(self.serializer_class(storeqrcode).data, status=status.HTTP_200_OK)
        else:
            r = requests.get(
                'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % (
                    appid, secret)).json()
            access_token = r.get("access_token", "")
            if access_token:
                store = serializer.validated_data['store']
                # 指定上传参数
                data = {
                    "path": serializer.validated_data['path'] + "?store=%s" % store.id,
                    "width": serializer.validated_data.get('width', 430)
                }

                # 发送请求，错误则返回所有信息
                res = requests.post("https://api.weixin.qq.com/wxa/getwxacode?access_token=%s" % access_token,
                                    json=data, headers={'Content-Type': "application/json"})
                if res.status_code == 200:
                    # 生成内容文件
                    content = ContentFile(res.content)
                    storeqrcode = models.StoreQRCode(**serializer.validated_data)
                    storeqrcode.save()
                    storeqrcode.QRCodeImage.save('%s.jpg' % str(uuid.uuid4()).replace('-', ''), content)

                    return Response(serializers.StoreQRCodeSerializer(storeqrcode).data, status=status.HTTP_201_CREATED)
                else:
                    return Response(res.json(), status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response(r, status=status.HTTP_400_BAD_REQUEST)


class StoreInfoView(RetrieveUpdateViewSets):
    """
       用于店铺信息查看与修改,此接口不在主接口显示
    """
    queryset = models.Stores.objects.all()
    serializer_class = serializers.StoreInfoSerializer
    permission_classes = (MerchantOrReadOnlyPermission,)

    def perform_update(self, serializer):
        longitude=serializer.validated_data.get('longitude','')
        latitude=serializer.validated_data.get('latitude','')
        if latitude and longitude:
            adcode = look_up_adocode('%6f,%6f' % (longitude,latitude))
            if adcode and DeliverAdcode.objects.filter(code=adcode).exists():
                serializer.save(adcode=adcode)
            else:
                return Response({'code':2004,'msg':'此区域无法进行配送'})
        else:
            serializer.save()


class EnterpriseQualificationView(RetrieveOnlyViewSets):
    """
        用于对应店铺资质的查看，此接口不在主接口显示
    """
    queryset = models.Stores.objects.all()
    serializer_class = serializers.EnterpriseQualificationSerializer


class StoreGoodsTypeView(CreateOnlyViewSet):
    """
        用于创建与修改店铺分类（名称，序号，日期）
    """
    serializer_class = serializers.StoreGoodsTypeSerializer
    permission_classes = (MerchantOrReadOnlyPermission,)

    def get_queryset(self):
        if self.request.user.is_staff:
            return models.StoreGoodsType.objects.all()
        elif self.request.user.is_authenticated:
            return models.StoreGoodsType.objects.filter(store=getattr(self.request.user, 'stores', 0))

        return models.StoreGoodsType.objects.none()


class PriceFilterClass(FilterSet):
    class Meta:
        model = GoodDetail
        fields = {
            'min_price': ['lte', 'gte'],
            'state': ['exact'],
            'title': ['exact', 'contains']
        }


class GoodsTypeView(ListDeleteViewSet):
    """
        用于将商品添加到店铺分类及删除对应店铺分类
    """
    serializer_class = serializers.GoodsTypeSerializer
    permission_classes = (MerchantOrReadOnlyPermission,)
    queryset = GoodDetail.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_class = PriceFilterClass
    filter_fields = ('title__contains', 'min_price__lte', 'min_price__gte', 'state')

    def list(self, request, *args, **kwargs):
        store_id = self.request.query_params.get('store', '0')
        good_type = self.request.query_params.get('good_type', '')
        serializer_class = serializers.GoodDetailSerializer
        try:
            store_id = int(store_id)
            store = models.Stores.objects.get(pk=store_id)
            # 不加good_type返回类型，good_type=0返回所有，good_type=null返回未分类，其他返回筛选结果
            if good_type == '':
                queryset = models.GoodsType.objects.filter(store_goods_type__store_id=store_id)
                serializer_class = serializers.GoodsTypeSerializer
            elif good_type == '0':
                queryset = self.filter_queryset(GoodDetail.objects.filter(store_id=store_id))
            elif good_type == 'null':
                queryset = self.filter_queryset(GoodDetail.objects.filter(store_id=store_id, good_type_id=None))
            else:
                good_type_id = int(good_type)
                queryset = self.filter_queryset(GoodDetail.objects.filter(store_id=store_id, good_type_id=good_type_id))

        except ValueError:
            queryset = GoodDetail.objects.none()
            store_ret=None

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializer_class(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=True, serializer_class=serializers.AddGoodsSerializer)
    def add_goods(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        good_ids = set(serializer.validated_data.get('good_list', []))
        put_on_sale_ids = set(serializer.validated_data.get('put_on_sale_list', []))
        owner_good_ids = list(GoodDetail.objects.filter(owner=request.user).values_list('id', flat=True))
        if good_ids and good_ids.issubset(owner_good_ids):
            if models.GoodsType.objects.filter(pk=pk).exists():
                good_type = models.GoodsType.objects.get(pk=pk)
                if good_type.store_goods_type.store == request.user.stores:
                    GoodDetail.objects.filter(id__in=good_ids).update(good_type=good_type)
            else:
                return Response('不存在此type')
        if put_on_sale_ids and put_on_sale_ids.issubset(owner_good_ids):
            op = request.query_params.get('op', 'upper')
            if op == 'upper':
                GoodDetail.objects.filter(id__in=put_on_sale_ids).update(state=0)
            elif op == 'lower':
                GoodDetail.objects.filter(id__in=put_on_sale_ids).update(state=1)
        return Response('ok')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_destroy_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_destroy_object(self):
        queryset=models.GoodsType.objects.all()
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj


class StoreSearchView(ListOnlyViewSet):
    queryset = models.Stores.objects.filter(active_state=1)
    serializer_class = serializers.StoreSearchSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        queryset = self.queryset
        q = self.request.query_params.get('q', '')
        first_class = self.request.query_params.get('first_class','')

        if q:
            queryset = queryset.filter(name__contains=q)
            if self.request.user.is_authenticated:
                SearchHistory.objects.update_or_create(defaults={
                    'user': self.request.user, 'q': q
                }, user=self.request.user, q=q)

        if first_class:
            try:
                first_class = int(first_class)
                queryset = queryset.filter(goods__third_class__second_class__first_class_id=first_class).distinct()
            except ValueError:
                pass
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(sorted(filter(lambda x:x.get('distance',0)<=5,serializer.data),key=lambda x:x.get('distance',0)))

        serializer = self.get_serializer(queryset, many=True)
        return Response(sorted(filter(lambda x:x.get('distance',0)<=5,serializer.data),key=lambda x:x.get('distance',0)))


class StoreMessageView(RetrieveOnlyViewSets):
    queryset = models.Stores.objects.filter(active_state=1)
    serializer_class = serializers.StoreMessageSerializer