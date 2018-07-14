import datetime

from django.db.models import F

from rest_framework.views import Response, status
from rest_framework.viewsets import ModelViewSet

# Create your views here.

from . import serializers, models
from goods.models import SKU
from tools.permissions import MerchantOrReadOnlyPermission
from tools.viewset import CreateListDeleteViewSet, CreateListViewSet, ListOnlyViewSet, CreateOnlyViewSet


class ShoppingCarItemView(ModelViewSet):
    """
        修改、删除具体购物车项
    """
    serializer_class = serializers.ShoppingCarItemSerializer
    queryset = models.ShoppingCarItem.objects.all()

    def perform_create(self, serializer):
        price_added = serializer.validated_data['sku'].price
        total_money = serializer.validated_data['num'] * price_added
        serializer.save(user=self.request.user, price_of_added=price_added, total_money=total_money)

    def list(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            queryset = models.ShoppingCarItem.objects.filter(shopping_car__user=self.request.user, num__gt=0)
        else:
            queryset = models.ShoppingCarItem.objects.none()
        return queryset

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        sku_id = request.data.get('sku')
        try:
            sku_id = int(sku_id)
        except ValueError:
            return Response("必须填写SKU", status=status.HTTP_400_BAD_REQUEST)

        if instance.sku.id != sku_id:
            instance.delete()
            return Response({'code': 4005, 'msg': '对象重复删除'})
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class ShoppingCarView(ListOnlyViewSet):
    serializer_class = serializers.ShoppingCarSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            queryset = models.ShoppingCar.objects.filter(user=self.request.user)
        else:
            return models.ShoppingCar.objects.none()

        return queryset


class CouponView(CreateListDeleteViewSet):
    """
        查看创建及删除店铺优惠券
    """
    serializer_class = serializers.CouponSerializer
    permission_classes = (MerchantOrReadOnlyPermission,)

    def get_queryset(self):
        store_id = self.request.query_params.get('store', '')
        today = datetime.date.today()
        try:
            store_id = int(store_id)
        except ValueError:
            return models.Coupon.objects.none()
        if hasattr(self.request.user, 'stores'):
            own_store = getattr(self.request.user, 'stores')
            op = self.request.query_params.get('op')
            if op == 'backend' and own_store.id == store_id:
                return models.Coupon.objects.filter(store_id=store_id)

        return models.Coupon.objects.filter(store_id=store_id, date_from__lte=today, date_to__gte=today,
                                            available_num__gt=0)

    def perform_create(self, serializer):
        serializer.save(store=self.request.user.stores)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.available_num = 0
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetCouponView(CreateListViewSet):
    """
        普通用户获取有效优惠券列表，领取优惠券
    """
    serializer_class = serializers.GetCouponSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        coupon = serializer.validated_data['coupon']
        today = datetime.date.today()

        if coupon.date_from <= today and coupon.date_to >= today and coupon.available_num > 0:
            if models.GetCoupon.objects.filter(user=self.request.user, coupon=coupon).exists():
                user_coupon = models.GetCoupon.objects.filter(user=self.request.user, coupon=coupon)[0]
                if user_coupon.has_num >= coupon.limit_per_user:
                    return Response({'code': 4003, "msg": '你可领的券数超限'})
            self.perform_create(serializer)
            coupon.available_num = F('available_num') - 1
            coupon.save()
            headers = self.get_success_headers(serializer.data)
            return Response({"msg": "优惠券领取成功", "code": 1000}, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response({"msg": '该券不可领取或可领取数量为0', "code": 4004})

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            today = datetime.date.today()
            queryset = models.GetCoupon.objects.filter(user=self.request.user, coupon__date_from__lte=today,
                                                       coupon__date_to__gte=today)
        else:
            queryset = models.GetCoupon.objects.none()
        return queryset


class StoreActivityView(CreateListDeleteViewSet):
    """
        查看、创建、删除店铺活动
    """
    serializer_class = serializers.StoreActivitySerializer
    queryset = models.StoreActivity.objects.all()
    permission_classes = (MerchantOrReadOnlyPermission,)

    def perform_create(self, serializer):
        serializer.save(store=self.request.user.stores)

    def get_queryset(self):
        store_id = self.request.query_params.get('store', '')
        now = datetime.datetime.now()
        try:
            store_id = int(store_id)
        except ValueError:
            return models.StoreActivity.objects.none()
        if hasattr(self.request.user, 'stores'):
            own_store = getattr(self.request.user, 'stores')
            op = self.request.query_params.get('op')
            if op == 'backend' and own_store.id == store_id:
                return models.StoreActivity.objects.filter(store_id=store_id)

        return models.StoreActivity.objects.filter(store_id=store_id, datetime_from__lte=now, datetime_to__gte=now,
                                                   state=0)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.state = 1
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BalanceView(CreateOnlyViewSet):
    serializer_class = serializers.BalanceSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        stores = serializer.validated_data['stores']
        ret = []
        for st in stores:
            store = st['store']

            # 判断是否为该店铺下的sku，如果不属于指定店铺直接报错
            sku_data = st['skus']
            sku_ids = [item['sku'].id for item in sku_data]
            if not SKU.objects.filter(id__in=sku_ids, color__good_detail__store=store).exists():
                return Response('sku所属店铺出错', status=status.HTTP_400_BAD_REQUEST)

            # 取出店铺的所有有效活动
            now = datetime.datetime.now()
            activities = models.StoreActivity.objects.filter(store=store, datetime_from__lte=now, datetime_to__gte=now,
                                                             state=0)
            # 计算每个活动的优惠金额

            ac = []
            for activity in activities:
                # 取出所有可参与活动的sku
                fit_sku = sku_data
                if not activity.select_all:
                    # 筛选时good要加id,筛选的结果要加list()
                    select_goods = activity.selected_goods.values_list('good', flat=True)
                    fit_sku = list(filter(lambda x: x['sku'].color.good_detail.id in select_goods, sku_data))

                if fit_sku:
                    items_num = sum([t['num'] for t in fit_sku])
                    items_money = sum([t['num'] * t['sku'].price for t in fit_sku])

                    x, y = activity.algorithm(items_num, items_money)
                    # 将优惠大于0的信息返回
                    if y>0:
                        ac.append({'id': activity.id, 'activity': x, 'reduction_money': y, 'item_num': items_num,
                                    'items_money': items_money,'type':'activity'})
            # 返回优惠券信息
            cost_price = sum([t['num'] * t['sku'].price for t in sku_data])
            cost_num = sum([t['num'] for t in sku_data])
            today=datetime.date.today()
            if models.GetCoupon.objects.filter(user=request.user,coupon__store=store,has_num__gt=0,coupon__date_to__gte=today,coupon__date_from__lte=today).exists():
                user_coupons=models.GetCoupon.objects.filter(user=request.user,coupon__store=store,has_num__gt=0,coupon__date_to__gte=today,coupon__date_from__lte=today)
                for get_user_coupon in user_coupons:
                    coupon = get_user_coupon.coupon
                    x,y=coupon.algorithm(cost_price)
                    if y>0:
                        ac.append({'id':coupon.id,'activity':x,'reduction_money': y,'item_num': cost_num,
                                    'items_money': cost_price,'type':'coupon'})

            op =request.query_params.get('op')
            sd = []

            if op != 'update':
                # 附加SKU信息
                for sk in sku_data:
                    ser = serializers.SkuDetailSerializer(instance=sk['sku'])
                    ser_ = ser.data
                    ser_.update({'num': sk['num']})
                    sd.append(ser_)

            # 附加店铺信息
            ret.append({'store': {
                'id': store.id,
                'name': store.name,
                'logo': store.logo,
                'activities':sorted(ac,key=lambda x:x['reduction_money'],reverse=True) if ac else ac,
                'cost_num':cost_num,
                'cost_money':cost_price,
                'take_off': store.take_off,
                'skus':sd
            }})

        # 取出收货地址

        receive_address = models.ReceiveAddress.objects.filter(user=self.request.user,is_default=True)
        rec={'stores':ret,'receive_address':serializers.ReceiveAddressSerializer(receive_address,many=True).data}

        return Response(rec)


class ReceiveAddressViewSets(ModelViewSet):
    queryset = models.ReceiveAddress.objects.all()
    serializer_class = serializers.ReceiveAddressSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            queryset = models.ReceiveAddress.objects.filter(user=self.request.user)
        else:
            return models.ReceiveAddress.objects.none()

        return queryset

    def perform_create(self, serializer):
        is_default=serializer.validated_data['is_default']
        if is_default:
            models.ReceiveAddress.objects.filter(user=self.request.user).update(is_default=False)
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        is_default = serializer.validated_data['is_default']
        if is_default:
            models.ReceiveAddress.objects.filter(user=self.request.user).update(is_default=False)
        serializer.save(user=self.request.user)


class UnifyOrderView(ModelViewSet):
    queryset = models.UnifyOrder.objects.all()
    serializer_class = serializers.UnifyOrderSerializer

