from rest_framework.views import Response, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action

from django.utils.crypto import get_random_string
from django.conf import settings
from django.core.files.base import ContentFile
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet


from tools.viewset import CreateOnlyViewSet, ListDeleteViewSet, RetrieveOnlyViewSet
from tools.permissions import MerchantOrReadOnlyPermission

from guardian.shortcuts import assign_perm

import requests, uuid

# Create your views here.

from . import serializers, models
from index.models import Application
from goods.models import GoodDetail

appid = getattr(settings, 'APPID')
secret = getattr(settings, 'APPSECRET')


class GenerateCodeView(CreateOnlyViewSet):
    queryset = models.CodeWarehouse.objects.all()
    serializer_class = serializers.GenerateCodeSerializer
    permission_classes = (IsAdminUser,)

    def perform_create(self, serializer):
        code = get_random_string()
        while models.CodeWarehouse.objects.filter(code=code).exists():
            code = get_random_string()
        data = {
            'code': code,
            'use_state': 0
        }
        serializer.save(**data)


class StoresViewSets(ModelViewSet):
    serializer_class = serializers.StoresSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['active_code']
        application = serializer.validated_data['info']
        if application.application_status != 5:
            return Response('你的申请未通过,请通过后进行再验证', status=status.HTTP_400_BAD_REQUEST)

        if models.CodeWarehouse.objects.filter(code=code, use_state=0).exists():

            self.perform_create(serializer)
            application.codewarehouse.use_state = 1
            application.codewarehouse.active_user = request.user
            application.codewarehouse.save()
            Application.objects.filter(pk=application.pk).update(application_status=6)

            # 将申请用户加入权限组

            assign_perm('store.change_stores', request.user, request.user.stores)

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


class StatusChangeView(CreateOnlyViewSet):
    serializer_class = serializers.StatusChangeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = Application.objects.filter(application_id=serializer.validated_data['application_id'])
        if obj.exists():
            obj.update(application_status=serializer.validated_data['application_status'])

            return Response('success')
        else:
            return Response('Not exists', status=status.HTTP_400_BAD_REQUEST)


class DepositView(ModelViewSet):
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


class StoreInfoView(RetrieveOnlyViewSet):
    queryset = models.Stores.objects.all()
    serializer_class = serializers.StoreInfoSerializer


class EnterpriseQualificationView(RetrieveOnlyViewSet):
    queryset = models.Stores.objects.all()
    serializer_class = serializers.EnterpriseQualificationSerializer


class StoreGoodsTypeView(CreateOnlyViewSet):
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
        fields={
            'min_price':['lte','gte'],
            'state':['exact'],
            'title':['exact','contains']
        }


class GoodsTypeView(ListDeleteViewSet):
    serializer_class = serializers.GoodDetailSerializer
    permission_classes = (MerchantOrReadOnlyPermission,)
    queryset = GoodDetail.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_class=PriceFilterClass
    filter_fields=('title__contains','min_price__lte','min_price__gte','state')

    def list(self, request, *args, **kwargs):
        store_id = self.request.query_params.get('store', '0')
        good_type = self.request.query_params.get('good_type', '')
        serializer_class = serializers.GoodDetailSerializer
        try:
            store_id = int(store_id)

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

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializer_class(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'],detail=True,serializer_class=serializers.AddGoodsSerializer)
    def add_goods(self,request,pk=None):
        if models.GoodsType.objects.filter(pk=pk).exists():
            good_type=models.GoodsType.objects.get(pk=pk)
            serializer=self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            ids=serializer.validated_data.get('good_list','')
            owner_good_ids=GoodDetail.objects.filter(owner=request.user)
            if ids in owner_good_ids:
                GoodDetail.objects.filter(id__in=ids).update(good_type=good_type)
                return Response('ok')
            else:
                return Response('你无权修改改id')
        else:
            return Response('不存在此type')
