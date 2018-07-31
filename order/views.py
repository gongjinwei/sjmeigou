import datetime, random, time
from decimal import Decimal

from django.db.models import F, Q

from rest_framework.views import Response, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from django_redis import get_redis_connection
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.query import EmptyQuerySet

# Create your views here.

from . import serializers, models
from goods.models import SKU
from tools.permissions import MerchantOrReadOnlyPermission, MerchantPermission
from tools.viewset import CreateListDeleteViewSet, CreateListViewSet, ListOnlyViewSet, CreateOnlyViewSet, \
    ListDetailDeleteViewSet
from tools.contrib import get_deliver_pay, store_order_refund
from wxpay.views import weixinpay, dwd
from platforms.models import AccountRecharge, Account

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

    def perform_destroy(self, instance):
        shopping_car = instance.shopping_car
        instance.delete()
        if len(shopping_car.items.all())==0:
            shopping_car.delete()


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
        receive_address = models.ReceiveAddress.objects.filter(user=self.request.user, is_default=True)
        if receive_address.exists():
            destination = '%s,%s' % (receive_address[0].longitude, receive_address[0].latitude)
        else:
            destination = ''
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

            op = request.query_params.get('op', '')
            # sku信息收集
            sd = []

            if op != 'update':
                # 附加SKU信息
                for sk in sku_data:
                    ser = serializers.SkuDetailSerializer(instance=sk['sku'])
                    ser_ = ser.data
                    ser_.update({'num': sk['num']})
                    sd.append(ser_)

            # 计算配送费用
            origin = '%s,%s' % (store.longitude, store.latitude)

            delivery_pay, store_to_pay, deliver_distance = get_deliver_pay(origin,
                                                                           destination) if origin and destination else (
                0, 0, None)
            store_delivery_charge, created = Account.objects.get_or_create(user=None, store=store, account_type=5)

            has_enough_delivery = store_delivery_charge.bank_balance >= Decimal(20.00)
            # 附加店铺信息
            ret.append({'store': {
                'id': store.id,
                'name': store.name,
                'logo': store.logo,
                'activities': sorted(ac, key=lambda x: x['reduction_money'], reverse=True) if ac else ac,
                'cost_num': cost_num,
                'cost_money': cost_price,
                'take_off': store.take_off,
                'skus': sd,
                "deliver_pay": delivery_pay,
                'has_enough_delivery': has_enough_delivery,
                'deliver_distance': deliver_distance
            }})

        # 取出收货地址

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


def prepare_payment(user, body, account, order_no, order_type=None):
    order_trade = models.OrderTrade()
    order_trade.trade_no = order_trade.trade_number
    if order_type == 'unify_order':
        order_trade.unify_order = models.UnifyOrder.objects.get(pk=order_no)

    elif order_type == "store_order":
        order_trade.store_order = models.StoreOrder.objects.get(pk=order_no)

    elif order_type == "recharge":
        order_trade.recharge = AccountRecharge.objects.get(pk=order_no)

    res = weixinpay.unified_order(trade_type="JSAPI", openid=user.userinfo.openId, body=body,
                                  total_fee=int(account * 100), out_trade_no=order_trade.trade_no)

    if res.get('return_code') == "SUCCESS":
        package = res.get('prepay_id')
        data = {
            "appId": weixinpay.app_id,
            "timeStamp": str(int(time.time())),
            "nonceStr": weixinpay.nonce_str,
            "package": "prepay_id=%s" % package,
            "signType": "MD5"
        }

        order_trade.save()
        data.update(paySign=weixinpay.sign(data), trade=order_trade, user=user)
        models.InitiatePayment.objects.create(**data)
        data.pop('user')
        data.pop('trade')

        return data
    else:
        return res.get('return_msg')


class UnifyOrderView(CreateOnlyViewSet):
    queryset = models.UnifyOrder.objects.all()
    serializer_class = serializers.UnifyOrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not getattr(self.request.user, 'userinfo', None):
            return Response({'code': 4102, 'msg': '此用户没有在小程序注册', 'success': 'FAIL'})
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
                return Response({'code': 4101, 'msg': '下单金额必须大于0', 'success': 'FAIL'})

        # 有店铺订单的情况下
        else:

            for data_st in store_orders:
                store = data_st['store']
                sku_data = data_st.get('sku_orders', [])
                if not sku_data:
                    return Response({'code': 4105, 'msg': '必须添加店铺具体规格商品', 'success': 'FAIL'})
                # 验证库存
                has_no_stock = list(filter(lambda x: x['sku'].stock < x['num'], sku_data))
                if has_no_stock:
                    return Response({'code': 4107, 'msg': '库存不足', 'success': 'FAIL'})

                # 验证活动
                activity_discount = 0
                coupon_discount = 0
                activity = data_st.get('activity', None)
                get_coupon_data = data_st.get('coupon', None)
                deliver_server = data_st.get('deliver_server', None)
                store_deliver_payment = Decimal(0.00)
                store_to_pay = Decimal(0.00)
                deliver_distance = None

                # 计算物流费用
                if deliver_server:
                    if hasattr(deliver_server, 'server'):

                        # 选择了点我达
                        if deliver_server.server.id == 2:
                            # 验证商户物流账号余额
                            store_delivery_charge, created = Account.objects.get_or_create(user=None, store=store,
                                                                                           account_type=5)

                            if store_delivery_charge.bank_balance < Decimal(20.00):
                                return Response({'code': 4109, 'msg': '商户物流费用不足', 'success': 'FAIL'})

                            address = serializer.validated_data.get('address', None)
                            if not address:
                                return Response({'code': 4108, 'msg': '必须选择地址', 'success': 'FAIL'})
                            else:
                                destination = '%s,%s' % (address.longitude, address.latitude)
                                origin = '%s,%s' % (store.longitude, store.latitude)

                                store_deliver_payment, store_to_pay, deliver_distance = get_deliver_pay(origin,
                                                                                                        destination)

                if activity and get_coupon_data:
                    return Response({'code': 4106, 'msg': '只能使用一种优惠', 'success': 'FAIL'})
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
                    {'store_order_no': store_order_no, 'account': store_order_money, 'user': self.request.user,
                     'store_to_pay': store_to_pay, 'deliver_payment': store_deliver_payment,
                     'deliver_distance': deliver_distance})

                # 移除购物车
                shopping_car =models.ShoppingCar.objects.filter(user=self.request.user,store=store)
                if shopping_car.exists():
                    shopping_car = shopping_car[0]

                    models.ShoppingCarItem.objects.filter(shopping_car=shopping_car,sku__in=skus).delete()
                    if len(shopping_car.items.all()) ==0:
                        shopping_car.delete()

        # 统一下单
        if order_money != price:
            return Response({'code': 4107, 'msg': '下单价格不符', 'success': 'FAIL'})

        account = order_money
        serializer.validated_data.update({
            'account': account,
            'order_no': order_no
        })

        self.perform_create(serializer)

        # 生成总的待付款信息

        ret = prepare_payment(self.request.user, body, account, order_no, order_type='unify_order')

        return Response({"code": 1000, 'msg': '下单成功', "data": ret})

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
            if order.state == 2 or order.state == 3:
                order.state = 4
                order.save()
                # 商家将收到余额
                return Response({'code': 1000, 'msg': '收货成功', "return_code": "SUCCESS"})
            else:
                return Response({'code': 4201, 'msg': '此状态无法收货', "return_code": "FAIL"})
        elif op == 2 and order.user == user and order.state ==1:
                order.state = 8
                order.save()
                return Response({'code': 1000, 'msg': '取消成功', "return_code": "SUCCESS"})

        elif op == 3 and order.store == user.stores and order.state == 7:
            # 平台进入退款操作，成功后更新状态
            order.state = 6
            order.save()
            return Response({'code': 1000, 'msg': '退款成功', "return_code": "SUCCESS"})

        return Response({'code': 4210, 'msg': '未知操作', "return_code": "FAIL"})

    @action(methods=['post'], detail=True, serializer_class=serializers.StorePriceChangeSerializer,
            permission_classes=(MerchantPermission,))
    def change_price(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.get_object()
        to_price = serializer.validated_data.get('price')
        if to_price >= 0 and instance.state == 1 and instance.account > to_price and instance.store == self.request.user.stores:

            # 再次发起付款
            instance.account = to_price
            instance.save()
            return Response({'code': 1000, 'msg': '改价成功', "return_code": "SUCCESS"})

        else:
            return Response({'code': 4202, 'msg': '订单必须是待付款状态，且价格只能改低'})

    @action(methods=['get'], detail=True)
    def check_delivery(self, request, pk=None):
        order = self.get_object()
        te = request.query_params.get('test', '')
        te_option = {
            'accept': 'order_accept_test',
            'arrive': 'order_arrive_test',
            'fetch': "order_fetch_test",
            "finish": 'order_finish_test'
        }
        if te and te_option.get(te, '') and hasattr(dwd, te_option.get(te)):
            getattr(dwd, te_option.get(te))(pk)
        ret = dwd.order_get(pk)
        return Response(ret)

    @action(methods=['get'], detail=True)
    def check_rider(self, request, pk=None):
        store_order = self.get_object()
        if not models.DwdOrder.objects.filter(store_order=store_order).exists():
            return Response({'errorCode': '3001', 'msg': '该物流单不存在'})
        dwd_order = models.DwdOrder.objects.get(store_order=store_order)
        ret = dwd.order_rider_position(pk, dwd_order.rider_code)
        # 只有骑手位置正确返回时才返回相应结果
        if ret.get("errorCode", '') == "0":
            dwd_order_serializer = serializers.DwdRiderSerializer(instance=dwd_order)
            ret.update(dwd_order_serializer.data)
        ori_dis = {
            "seller_lat": store_order.store.latitude,
            "seller_lng": store_order.store.longitude,
            "seller_name": store_order.store.name,
            "seller_logo": store_order.store.logo,
            "seller_contract": store_order.store.store_phone,
            "rider_mobile":dwd_order.rider_mobile,
            "receiver_lat": store_order.unify_order.address.latitude,
            "receiver_lng": store_order.unify_order.address.longitude
        }
        ret.update(ori_dis)
        return Response(ret)

    @action(methods=['post'], detail=True, serializer_class=serializers.CommentImageSerializer)
    def add_comment_image(self, request, pk=None):
        store_order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(store_order=store_order, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['get', 'post'], detail=True, serializer_class=serializers.CommentContentSerializer)
    def add_comment(self, request, pk=None):
        store_order = self.get_object()
        if request.method == 'GET':
            ret = {}
            dwd_order = getattr(store_order, 'dwd_order_info', None)
            if dwd_order and request.query_params.get('op', '') != 'backend':
                ret['dwd_order'] = {
                    'id': dwd_order.id,
                    "rider_name": dwd_order.rider_name,
                    "arrive_time": dwd_order.arrive_time
                }
                ret['commentator'] = {
                    'logo': store_order.store.logo,
                    'name': store_order.store.name
                }
            elif request.query_params.get('op', '') == 'backend':
                ret['commentator'] = {
                    'logo': store_order.user.userinfo.avatarUrl,
                    'name': store_order.user.userinfo.nickName
                }
            return Response(ret)
        elif request.method == 'POST':
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            if store_order.state != 4:
                return Response({"code": 4203, "msg": '该状态不能被评价', "success": "FAIL"})
            op = request.query_params.get('op', '')
            if op == 'backend' and models.OrderComment.objects.filter(order=store_order, state__in=[2, 3]).exists():
                return Response({'code': 4204, "msg": "您已评价过了", 'success': 'FAIL'})
            elif not op and models.OrderComment.objects.filter(order=store_order, state__in=[1, 3]).exists():
                return Response({'code': 4204, "msg": "您已评价过了", 'success': 'FAIL'})
            serializer.save(order=store_order)
            return Response({"code": 1000, "msg": '评价成功', "success": "SUCCESS"}, status=status.HTTP_201_CREATED)

    @action(methods=['post'], detail=True, serializer_class=serializers.ChangeDwdArriveTimeSerializer)
    def change_arrive_time(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        store_order = self.get_object()
        dwd_order = serializer.validated_data['dwd_order']
        arrive_time = serializer.validated_data['arrive_time']
        op = request.query_params.get('op', '')
        if op != 'backend' and dwd_order.store_order == store_order:
            dwd_order.user_arrive_time = arrive_time
            return Response({'code': 1000, 'msg': '修改成功'})
        else:
            return Response({'code': 4206, 'msg': '您无此权限'})

    @action(methods=['post'], detail=True, serializer_class=serializers.OrderRefundSerializer)
    def refund(self, request, pk=None):
        store_order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if request.query_params.get('op', '') == 'backend':
            return Response({'code': 4207, 'msg': '商户不能发起退款'})

        refund_fee = serializer.validated_data['refund_money']
        code, msg = store_order_refund(models.OrderTrade, models.OrderRefundResult, store_order, refund_fee)
        serializer.save(store_order=store_order,state=1)
        return Response({'code': code, 'msg': msg})

    @action(methods=['post'],detail=True,serializer_class=serializers.OrderReviewSerializer)
    def add_review(self,request,pk=None):
        store_order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user,order=store_order)

        return Response({'code':1000,'msg':'追评成功'})


class InitialPaymentView(CreateOnlyViewSet):
    serializer_class = serializers.InitialTradeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.validated_data['order']
        ret = prepare_payment(order.user, order.unify_order.order_desc, order.account, order.store_order_no,
                              order_type='store_order')
        return Response(ret)
