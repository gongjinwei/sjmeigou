import random,datetime,requests, uuid,decimal

from rest_framework.views import Response, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser,AllowAny,IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404

from django.conf import settings
from django.core.files.base import ContentFile
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet
from django.db.models import Min

from guardian.shortcuts import assign_perm

from tools.viewset import CreateOnlyViewSet, ListDeleteViewSet, RetrieveUpdateViewSets,RetrieveOnlyViewSets,ListOnlyViewSet,CreateListViewSet
from tools.permissions import MerchantOrReadOnlyPermission
from tools.contrib import look_up_adocode,get_deliver_pay,customer_get_object


# Create your views here.

from . import serializers, models
from index.models import Application
from goods.models import GoodDetail,SearchHistory
from platforms.models import CodeWarehouse,Account,DeliverAdcode
from register.models import UserInfo
from order.models import ReceiveAddress,OrderTrade
from order.serializers import SkuDetailSerializer,ReceiveAddressSerializer
from order.views import get_order_no,prepare_payment

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


class StoreFavoritesViewSets(CreateListViewSet):
    queryset = models.StoreFavorites.objects.all()
    serializer_class = serializers.StoreFavoritesSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if models.StoreFavorites.objects.filter(store=serializer.validated_data['store'],user=self.request.user).exists():
            models.StoreFavorites.objects.filter(store=serializer.validated_data['store'], user=self.request.user).delete()
            return Response({'code':1000,'msg':'成功取消关注'})
        else:
            serializer.save(user=self.request.user)
            return Response({'code': 1000, 'msg': '关注成功'})

    def get_queryset(self):
        queryset = self.queryset
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
        else:
            return queryset.none()

    @action(methods=['post'],detail=False,serializer_class=serializers.HistoryDeleteSerializer)
    def bulk_delete(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data['ids']
        user_ids = list(self.queryset.filter(user=request.user).values_list('id',flat=True))
        if set(ids).issubset(user_ids):
            self.queryset.filter(id__in=ids).delete()
            return Response({'code':1000,'msg':'删除成功'})
        else:
            return Response({'code':4150,'msg':'删除错误'})


class GoodFavoritesViewSets(CreateListViewSet):
    queryset = models.GoodFavorites.objects.all()
    serializer_class = serializers.GoodFavoritesSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if models.GoodFavorites.objects.filter(good=serializer.validated_data['good'],user=self.request.user).exists():
            models.GoodFavorites.objects.filter(good=serializer.validated_data['good'], user=self.request.user).delete()
            return Response({'code':1000,'msg':'成功取消收藏'})
        else:
            serializer.save(user=self.request.user)
            return Response({'code': 1000, 'msg': '收藏成功'})

    def get_queryset(self):
        queryset= self.queryset
        if hasattr(self.request,'user') and self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
        else:
            return queryset.none()

    @action(methods=['post'], detail=False, serializer_class=serializers.HistoryDeleteSerializer)
    def bulk_delete(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data['ids']
        user_ids = list(self.queryset.filter(user=request.user).values_list('id', flat=True))
        if set(ids).issubset(user_ids):
            self.queryset.filter(id__in=ids).delete()
            return Response({'code': 1000, 'msg': '删除成功'})
        else:
            return Response({'code': 4150, 'msg': '删除错误'})


class BargainActivityViewSets(ModelViewSet):
    queryset = models.BargainActivity.objects.filter()
    serializer_class = serializers.BargainActivitySerializer
    permission_classes = (MerchantOrReadOnlyPermission,)

    def perform_create(self, serializer):
        serializer.validated_data.update({'store':self.request.user.stores})
        origin_price = serializer.validated_data['sku'].price
        serializer.validated_data.update({'origin_price':origin_price})
        serializer.save()

    def get_queryset(self):
        queryset = self.queryset
        store_id = self.request.query_params.get('store','')
        op = self.request.query_params.get('op','')
        if store_id:
            try:
                store_id = int(store_id)
            except ValueError:
                return queryset.none()
            if models.Stores.objects.filter(pk=store_id).exists():
                store = models.Stores.objects.get(pk=store_id)
                now =datetime.datetime.now()
                if op != 'backend':
                    return queryset.filter(store=store,from_time__lte=now,to_time__gte=now,activity_stock__gt=0)
                else:
                    return queryset.filter(store=store)
        return queryset.none()


def check_bargain(user_bargain,receive_address,user_price,bargain_time,is_order=False):
    store = user_bargain.activity.store
    now = datetime.datetime.now()
    # 验证1：活动是否开始或终止，库存是否足够
    if user_bargain.activity.from_time > now:
        return 4251,'活动尚未开始',None
    if user_bargain.activity.to_time < now:
        return 4252, '活动已结束',None

    if user_bargain.activity.activity_stock <= 0:
        return 4253, '已经抢光了',None

    # 验证2：提交时的价格是否相符
    instant_min_price = models.HelpCutPrice.objects.filter(user_bargain=user_bargain,join_time__lte=bargain_time).aggregate(min_price=Min('instant_price'))['min_price']
    if not is_order and float(user_price) != instant_min_price:
        return 4254, '下单价格不符',None

    # 验证3：计算配送费用

    if receive_address:
        destination = '%6f,%6f' % (receive_address.longitude, receive_address.latitude)
    else:
        destination = ''

    origin = '%6f,%6f' % (store.longitude, store.latitude)

    delivery_pay, store_to_pay, deliver_distance = get_deliver_pay(origin,
                                                                   destination) if origin and destination else (
        0, 0, None)

    if is_order and instant_min_price+delivery_pay !=float(user_price):
        return 4254, '下单价格不符', None

    store_delivery_charge, created = Account.objects.get_or_create(user=None, store=store, account_type=5)

    has_enough_delivery = store_delivery_charge.bank_balance >= decimal.Decimal(20.00) and store_delivery_charge.bank_balance>decimal.Decimal(store_to_pay)

    return 1000,'OK',(delivery_pay,deliver_distance,has_enough_delivery)


class UserBargainViewSets(ModelViewSet):
    queryset = models.UserBargain.objects.all()
    serializer_class = serializers.UserBargainSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        activity = serializer.validated_data['activity']
        user = self.request.user
        price_now = activity.origin_price
        if self.queryset.filter(user=user, activity=activity).exists():
            return Response({'code': 4181, 'msg': '您已经创建过了'})
        instance = serializer.save(user=user, price_now=price_now)
        self.save_random_cut(instance, activity, user.userinfo,created=True)
        return Response({'code':1000,'msg':'创建成功'})

    @action(methods=['get','post'], detail=True,serializer_class=serializers.HelpCutPriceSerializer,permission_classes=[AllowAny])
    def cut_price(self, request, pk=None):
        obj = customer_get_object(self)
        user_id = request.query_params.get('userId', '')
        if user_id and UserInfo.objects.filter(pk=user_id).exists():
            userId = UserInfo.objects.get(pk=user_id)
        elif hasattr(request, 'user') and request.user.is_authenticated:
            userId = request.user.userinfo
        else:
            return Response({'code': 4182, 'msg': '请携带ID访问'})
        if request.method=='POST':
            activity = obj.activity

            code,msg,cut_price,price_now=self.save_random_cut(obj,activity,userId)

            return Response({'code':code, 'msg': msg, 'cut_price': cut_price, 'price_now': price_now})
        elif request.method =='GET':
            data = serializers.UserBargainSerializer(obj,context={'request':request}).data
            data['had_cut']=False
            if models.HelpCutPrice.objects.filter(userId=userId,user_bargain=obj).exists():

                data.update({'had_cut':True})
            return Response({'code':1000,'data':data})

    @action(methods=['get'], detail=True, serializer_class=serializers.HelpCutPriceSerializer)
    def get_help_cuts(self,request,pk=None):
        obj = customer_get_object(self)
        queryset = models.HelpCutPrice.objects.filter(user_bargain=obj)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=True, serializer_class=serializers.BargainBalanceSerializer)
    def bargain_balance(self,request,pk=None):
        user_bargain = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if user_bargain.user !=request.user:
            return Response({'msg':'非发起者不能结算','code':4255,'data':None})
        user_price = serializer.validated_data['price']
        receive_address = ReceiveAddress.objects.filter(user=self.request.user, is_default=True)
        if receive_address.exists():
            receive_address = ReceiveAddress.objects.get(user=self.request.user,is_default=True)
        else:
            receive_address= None
        store = user_bargain.activity.store
        sku = user_bargain.activity.sku
        now = datetime.datetime.now()
        code, msg, data = check_bargain(user_bargain, receive_address,user_price,now)
        if code == 1000:
            delivery_pay, deliver_distance, has_enough_delivery = data

            sd = SkuDetailSerializer(sku).data
            data = {
                'id': store.id,
                'name': store.name,
                'logo': store.logo,
                'take_off': store.take_off,
                "deliver_pay": delivery_pay,
                'price_now':user_price,
                'skus': sd,
                'has_enough_delivery': has_enough_delivery,
                'deliver_distance': deliver_distance,
                'balance_time':now,
                'receive_address':ReceiveAddressSerializer(receive_address).data if receive_address else None
            }

        return Response({'code': code, 'msg': msg, 'data': data})

    def save_random_cut(self,obj,activity,userId,created=False):
        if not created:
            # 每人限砍一次
            if models.HelpCutPrice.objects.filter(userId=userId, user_bargain=obj).exists():
                return 4171,'您已经砍过了',0,obj.price_now
            now = datetime.datetime.now()
            if activity.from_time >= now:
                return 4173, '活动还未开始',0,obj.price_now
            if activity.to_time <= now:
                return 4174, '活动已经结束',0,obj.price_now
        cut_price = round(random.uniform(activity.cut_price_from, activity.cut_price_to), 1)
        price_now = round(obj.price_now - cut_price, 1)
        if price_now < activity.min_price:
            price_now = activity.min_price
            cut_price = obj.price_now - activity.min_price
        models.HelpCutPrice.objects.create(user_bargain=obj, cut_price=cut_price, userId=userId,instant_price=price_now)
        obj.price_now = price_now
        obj.save()
        return 1000,'OK',cut_price,price_now

    @action(methods=['post'], detail=True, serializer_class=serializers.BargainOrderSerializer)
    def order(self,request,pk=None):
        user_bargain=self.get_object()
        if user_bargain.had_paid == True:
            return Response({'code':4192,'msg':'这个订单已支付'})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        order_data = data.get('store_order')

        if user_bargain.user != request.user:
            return Response({'code': 4191, 'msg': '非发起者不能下单'})
        data.update({'user_bargain': user_bargain})
        price = data['price']
        store = user_bargain.activity.store
        receive_addr = order_data.get('user_address')
        code, msg, deliver_data = check_bargain(user_bargain, receive_addr, price, data['balance_time'], is_order=True)

        if code == 1000:
            delivery_pay, deliver_distance, has_enough_delivery = deliver_data
            if has_enough_delivery:

                order_data.update({
                    'account': price,
                    'store_order_no': get_order_no(store.id),
                    'deliver_payment': delivery_pay,
                    'deliver_distance': deliver_distance,
                    'user': request.user,
                    'store':store
                })
                bargain_order = serializer.save()
                # 记录交易
                order_trade = OrderTrade()
                order_trade.trade_no = order_trade.trade_number
                order_trade.store_order = bargain_order.store_order
                order_trade.save()
                # 发起付款
                data = prepare_payment(request.user, '砍价订单', price, bargain_order.store_order.store_order_no,
                                       order_type='store_order')

                return Response({'code': 1000, 'msg': '下单成功，即将发起付款', 'data': data})
            else:
                return Response({'code': code, 'msg': '商家费用不足'})
        else:
            return Response({'code': code, 'msg': msg})

    def get_queryset(self):
        queryset = self.queryset
        if hasattr(self.request,'user') and self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
        else:
            return queryset.none()

    @action(methods=['get'],detail=False)
    def delivery(self,request):
        data=['120.060956,29.328234','120.060534,29.32797','120.060291,29.327797','120.059819,29.32747',
              '120.059245,29.327222','120.058737,29.327029']
        seconds = int(datetime.datetime.now().timestamp()/5)
        lng, lat = data[seconds % 6].split(',')
        return Response({'lng':lng,'lat':lat})


class SharingReduceViewSets(CreateListViewSet):
    queryset = models.SharingReduceActivity.objects.filter()
    serializer_class = serializers.SharingReduceSerializer
    permission_classes = (MerchantOrReadOnlyPermission,)

    def perform_create(self, serializer):
        serializer.save(store=self.request.user.stores)

    def get_queryset(self):
        queryset = self.queryset
        if hasattr(self.request,'user') and hasattr(self.request.user,'stores'):
            return queryset.filter(store=self.request.user.stores)
        else:
            return queryset.none()

    @action(methods=['post'],detail=True,serializer_class=serializers.JoinSharingReduceSerializer,permission_classes=(AllowAny,))
    def join(self,request,pk=None):
        obj = self.get_object()
        return Response('ok')