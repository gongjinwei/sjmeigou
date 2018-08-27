# -*- coding:UTF-8 -*-
import math, datetime, random
import requests
from django.conf import settings
from django.core.cache import cache
from weixin.pay import WeixinPayError
from rest_framework.generics import get_object_or_404

gd_key = getattr(settings, 'GDKEY')


def get_deliver_pay(origin, destination):
    ret = cache.get('%s:%s' % (origin, destination))
    if not ret:
        url = 'https://restapi.amap.com/v4/direction/bicycling?origin={}&destination={}&key={}'.format(origin,
                                                                                                       destination,
                                                                                                       gd_key)
        res = requests.get(url)
        # 返回米
        paths = res.json()['data']['paths']
        meters = min(paths, key=lambda x: x['distance'])['distance']
        kilometers = math.ceil(meters / 1000)
        if kilometers <= 1:
            ret = (1, 1.5, meters)
        else:
            plat_to_pay = (2 + kilometers) / 2
            ret = (kilometers, plat_to_pay, meters)
        cache.set('%s:%s' % (origin, destination), ret, timeout=24 * 3600 * 7)
    return ret


def store_order_refund(store_order, refund_fee):
    from order.models import OrderRefundResult, OrderTrade
    now = datetime.datetime.now()
    total_fee = int(store_order.account_paid * 100)
    if OrderTrade.objects.filter(store_order=store_order).exists():
        order_trade = OrderTrade.objects.get(store_order=store_order, paid_money__isnull=False)
    elif OrderTrade.objects.filter(unify_order=store_order.unify_order).exists():
        order_trade = OrderTrade.objects.get(unify_order=store_order.unify_order, paid_money__isnull=False)
    else:
        return (4301, '无此支付单号')

    if refund_fee > total_fee:
        return (4304, '退款金额不能大于总金额')

    refund_data = {
        "total_fee": total_fee,
        "out_refund_no": datetime.datetime.strftime(now, 'TK%Y%m%d%H%M%S%f{}'.format(random.randint(10, 100))),
        "out_trade_no": order_trade.trade_no,
        "refund_fee": refund_fee
    }
    from wxpay.views import weixinpay
    try:
        ret = weixinpay.refund(**refund_data)
    except WeixinPayError as e:
        return (4305, e.args[0])
    if ret.get("return_code", '') == "SUCCESS":
        receive_sign = ret.pop('sign')
        mysign = weixinpay.sign(ret)
        if receive_sign == mysign:
            ret.pop('serializer', None)

            OrderRefundResult.objects.create(**ret)
            return (1000, "退款成功")
        else:
            return (4302, "退款异常")
    else:
        return (4303, ret)


def look_up_adocode(location):
    url = 'https://restapi.amap.com/v3/geocode/regeo?key=%s&location=%s' % (gd_key, location)
    r = requests.get(url).json()
    if r['status'] == '1':
        return r['regeocode']['addressComponent']['adcode'][:4] + '00'


def look_up_towncode(location):
    url = 'https://restapi.amap.com/v3/geocode/regeo?key=%s&location=%s' % (gd_key, location)
    r = requests.get(url).json()
    if r['status'] == '1':
        return r['regeocode']['addressComponent'].get('towncode', None)


def prepare_dwd_order(store_order, user, op=None):
    from delivery.models import InitDwdOrder
    dwdorder = InitDwdOrder()
    receive_address = store_order.unify_order.address if store_order.unify_order else store_order.user_address
    store = store_order.store
    temp_dict = {
        'order_original_id': dwdorder.trade_number,
        'order_create_time': int(store_order.paid_time.timestamp() * 1000),
        'order_remark': '',
        'order_price': int(store_order.account_paid * 100),
        'cargo_weight': 0,
        'cargo_num': 1,
        'city_code': store.adcode,
        'seller_id': user.userinfo.id,
        'money_rider_needpaid': 0,
        'money_rider_prepaid': 0,
        'money_rider_charge': 0,
        'time_waiting_at_seller': 300,
        'delivery_fee_from_seller': 0
    }
    if op == 'backend' and hasattr(user, 'stores') and store_order.store == user.stores:
        temp_dict.update({
            'seller_name': store.info.contract_name,
            'seller_mobile': store.info.contract_mobile,
            'seller_address': store.receive_address,
            'seller_lat': round(store.latitude, 6),
            'seller_lng': round(store.longitude, 6),
            'consignee_name': receive_address.contact,
            'consignee_mobile': receive_address.phone,
            'consignee_address': receive_address.address + receive_address.room_no,
            'consignee_lat': round(receive_address.latitude, 6),
            'consignee_lng': round(receive_address.longitude, 6)
        })

    elif op != 'backend' and store_order.user == user:
        temp_dict.update({
            'seller_name': receive_address.contact,
            'seller_mobile': receive_address.phone,
            'seller_address': receive_address.address + receive_address.room_no,
            'seller_lat': round(receive_address.latitude, 6),
            'seller_lng': round(receive_address.longitude, 6),
            'consignee_name': store.info.contract_name,
            'consignee_mobile': store.info.contract_mobile,
            'consignee_address': store.receive_address,
            'consignee_lat': round(store.latitude, 6),
            'consignee_lng': round(store.longitude, 6)
        })
    dwdorder.__dict__.update(temp_dict)
    return dwdorder


def customer_get_object(self):
    queryset = self.queryset
    lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

    assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
    )

    filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
    obj = get_object_or_404(queryset, **filter_kwargs)
    return obj



