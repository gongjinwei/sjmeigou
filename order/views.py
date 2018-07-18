import datetime, random, time
from decimal import Decimal
from django.db.models import F, Q

from rest_framework.views import Response, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from django_redis import get_redis_connection
from django_filters.rest_framework import DjangoFilterBackend

# Create your views here.

from . import serializers, models
from goods.models import SKU
from tools.permissions import MerchantOrReadOnlyPermission
from tools.viewset import CreateListDeleteViewSet, CreateListViewSet, ListOnlyViewSet, CreateOnlyViewSet, \
    ListDetailDeleteViewSet
from wxpay.views import weixinpay

client = get_redis_connection()


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
                    if y > 0:
                        ac.append({'id': activity.id, 'activity': x, 'reduction_money': y, 'item_num': items_num,
                                   'items_money': items_money, 'type': 'activity'})
            # 返回优惠券信息
            cost_price = sum([t['num'] * t['sku'].price for t in sku_data])
            cost_num = sum([t['num'] for t in sku_data])
            today = datetime.date.today()
            if models.GetCoupon.objects.filter(user=request.user, coupon__store=store, has_num__gt=0,
                                               coupon__date_to__gte=today, coupon__date_from__lte=today).exists():
                user_coupons = models.GetCoupon.objects.filter(user=request.user, coupon__store=store, has_num__gt=0,
                                                               coupon__date_to__gte=today, coupon__date_from__lte=today)
                for get_user_coupon in user_coupons:
                    coupon = get_user_coupon.coupon
                    x, y = coupon.algorithm(cost_price)
                    if y > 0:
                        ac.append({'id': coupon.id, 'activity': x, 'reduction_money': y, 'item_num': cost_num,
                                   'items_money': cost_price, 'type': 'coupon'})

            op = request.query_params.get('op')
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
                'activities': sorted(ac, key=lambda x: x['reduction_money'], reverse=True) if ac else ac,
                'cost_num': cost_num,
                'cost_money': cost_price,
                'take_off': store.take_off,
                'skus': sd
            }})

        # 取出收货地址

        receive_address = models.ReceiveAddress.objects.filter(user=self.request.user, is_default=True)
        rec = {'stores': ret, 'receive_address': serializers.ReceiveAddressSerializer(receive_address, many=True).data}

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
        is_default = serializer.validated_data['is_default']
        if is_default:
            models.ReceiveAddress.objects.filter(user=self.request.user).update(is_default=False)
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        is_default = serializer.validated_data['is_default']
        if is_default:
            models.ReceiveAddress.objects.filter(user=self.request.user).update(is_default=False)
        serializer.save(user=self.request.user)


# 缓存取号
def get_order_no(store_id):
    today_key = '%s%s' % (1000 + store_id, datetime.datetime.strftime(datetime.datetime.now(), '%y%m%d'))
    if not client.exists(today_key):
        for i in range(1, 11):
            client.lpush(today_key, i)
    x, y = client.brpop(today_key, timeout=30)
    n = int(y)

    client.lpush(today_key, n + 10)

    ret = '%s%06d%s' % (today_key, n, random.randint(10, 100))
    return ret


def prepare_payment(user, body, account, order_no, order_type='unify_order'):
    res = weixinpay.unified_order(trade_type="JSAPI", openid=user.userinfo.openId, body=body,
                                  total_fee=int(account * 100), out_trade_no=order_no)

    if res.get('return_code') == "SUCCESS":
        package = res.get('prepay_id')
        data = {
            "appId": weixinpay.app_id,
            "timeStamp": str(int(time.time())),
            "nonceStr": weixinpay.nonce_str,
            "package": "prepay_id=%s" % package,
            "signType": "MD5"
        }
        if order_type == 'unify_order':
            data.update(paySign=weixinpay.sign(data), unify_order_id=order_no, user=user)
        else:
            data.update(paySign=weixinpay.sign(data), store_order_id=order_no, user=user)

        models.InitiatePayment.objects.create(**data)
        data.pop('user')
        return data
    else:
        return res.get('return_msg')


class UnifyOrderView(CreateOnlyViewSet):
    queryset = models.UnifyOrder.objects.all()
    serializer_class = serializers.UnifyOrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        store_payment = []
        if not getattr(self.request.user, 'userinfo', None):
            return Response({'code': 4102, 'msg': '此用户没有在小程序注册', 'success': 'failure'})
        price = serializer.validated_data.get('price', 0)

        body = serializer.validated_data.get('order_desc')
        order_no = get_order_no(0)
        order_num = 0
        order_money = 0
        store_orders = serializer.validated_data.get('store_orders', [])
        # 判断是否有店铺订单
        if not store_orders:
            # 验证价格大于0
            order_money = price
            if not price:
                return Response({'code': 4101, 'msg': '下单金额必须大于0', 'success': 'failure'})

        # 有店铺订单的情况下
        else:

            for data_st in store_orders:
                store = data_st['store']
                sku_data = data_st.get('sku_orders', [])
                if not sku_data:
                    return Response({'code': 4105, 'msg': '必须添加店铺具体规格商品', 'success': 'failure'})

                # 验证活动
                activity_discount = 0
                coupon_discount = 0
                activity = data_st.get('activity', None)
                get_coupon_data = data_st.get('coupon', None)
                store_deliver_payment = data_st.get('deliver_payment', Decimal(0.00))
                if activity and get_coupon_data:
                    return Response({'code': 4106, 'msg': '只能使用一种优惠', 'success': 'failure'})
                now = datetime.datetime.now()
                today = datetime.date.today()

                store_num = sum([s['num'] for s in sku_data])
                store_money = sum([s['num'] * s['sku'].price for s in sku_data]) + store_deliver_payment
                skus = [s['sku'] for s in sku_data]
                if activity and activity.store == store and activity.datetime_from <= now and activity.datetime_to >= now and activity.state == 0:
                    fit_sku = sku_data
                    if not activity.select_all:
                        # 筛选时good要加id,筛选的结果要加list()
                        select_goods = activity.selected_goods.values_list('good', flat=True)
                        fit_sku = list(filter(lambda x: x['sku'].color.good_detail.id in select_goods, sku_data))

                    if fit_sku:
                        items_num = sum([t['num'] for t in fit_sku])
                        items_money = sum([t['num'] * t['sku'].price for t in fit_sku])

                        x, activity_discount = activity.algorithm(items_num, items_money)

                # 验证优惠券

                if get_coupon_data and get_coupon_data.user == self.request.user and get_coupon_data.has_num > 0 and get_coupon_data.coupon.date_from <= today and get_coupon_data.coupon >= today:
                    coupon = get_coupon_data.coupon
                    x, coupon_discount = coupon.algorithm(store_money)

                store_order_no = get_order_no(store.id)
                store_order_money = store_money - activity_discount - coupon_discount
                order_num += store_num
                order_money += store_order_money
                data_st.update(
                    {'store_order_no': store_order_no, 'account': store_order_money, 'user': self.request.user})

                # 准备下单
                store_payment.append({
                    "user": self.request.user,
                    "body": body,
                    "account": store_order_money,
                    "order_no": store_order_no,
                    "order_type": "store_order"
                })

                # 移除购物车
                models.ShoppingCarItem.objects.filter(shopping_car__user=self.request.user, shopping_car__store=store,
                                                      sku__in=skus).delete()

        # 统一下单
        if order_money != price:
            return Response({'code': 4107, 'msg': '下单价格不符', 'success': 'failure'})

        account = order_money
        serializer.validated_data.update({
            'account': account,
            'order_no': order_no
        })

        self.perform_create(serializer)

        # 生成待付款信息

        ret = prepare_payment(self.request.user, body, account, order_no)
        for prepare in store_payment:
            prepare_payment(**prepare)

        return Response(ret)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StoreOrderView(ListDetailDeleteViewSet):
    serializer_class = serializers.StoreOrderSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('state', 'store_order_no')

    def get_queryset(self):
        op = self.request.query_params.get('op', '')
        if self.request.user.is_authenticated:
            if op == 'backend':
                return models.StoreOrder.objects.filter(store=self.request.user.stores)
            else:
                return models.StoreOrder.objects.filter(user=self.request.user)
        else:
            return models.StoreOrder.objects.none()

    def perform_destroy(self, instance):
        if instance.state == 8:
            instance.delete()
        elif instance.state == 5:
            instance.state = 9
            instance.save()
        else:
            return Response('此状态无法删除订单', status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=False)
    def state_change(self, request, serializer_class=serializers.StoreStateChangeSerializer):
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        op = serializer.validated_data['op']
        user = self.request.user
        order = serializer.validated_data['store_order']

        if op == 1 and order.user == user:
            if order.state==2 or order.state==3:
                order.state = 4
                order.save()
                return Response({'code':1000,'msg':'收获成功',"return_code":"SUCCESS"})
            else:
                return Response({'code':4201,'msg':'此状态无法收货',"return_code":"FAILURE"})
        elif op == 2 and order.user == user:
            if order.state == 1:
                order.state = 8
                order.save()
                return Response({'code': 1000, 'msg': '取消成功',"return_code":"SUCCESS"})
            elif order.state == 2:
                # 取消点我达订单,取消成功则更新状态
                order.state = 8
                order.save()
                return Response({'code': 1000, 'msg': '取消成功',"return_code":"SUCCESS"})
        elif op == 3 and order.store == user.stores and order.state==7:
            # 平台进入退款操作，成功后更新状态
            order.state = 6
            order.save()
            return Response({'code': 1000, 'msg': '退款成功',"return_code":"SUCCESS"})

        return Response({'code': 4210, 'msg': '未知操作',"return_code":"FAILURE"})

    @action(methods=['post'],detail=True,serializer_class=serializers.StoreStateChangeSerializer)
    def change_price(self,request,pk=None):
        instance = self.get_object()
        return Response(instance.account)


class InitialPaymentView(ListOnlyViewSet):
    serializer_class = serializers.InitiatePaymentSerializer

    def get_queryset(self):
        order_no = self.request.query_params.get('order', '')
        if self.request.user.is_authenticated:
            return models.InitiatePayment.objects.filter(user=self.request.user, store_order_id=order_no,
                                                         has_paid=False)
        else:
            return models.InitiatePayment.objects.none()
