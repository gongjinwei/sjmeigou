# -*- coding:UTF-8 -*-
import math, datetime, random
import requests
from django.conf import settings
from django.core.cache import cache
from wxpay.views import weixinpay

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


def store_order_refund(trade_model, result_model, store_order, refund_fee):
    now = datetime.datetime.now()
    total_fee = int(store_order.account_paid * 100)
    if trade_model.objects.filter(store_order=store_order).exists():
        order_trade = trade_model.objects.get(store_order=store_order, paid_money__isnull=False)
    elif trade_model.objects.filter(unify_order=store_order.unify_order):
        order_trade = trade_model.objects.get(unify_order=store_order.unify_order, paid_money__isnull=False)
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
    ret = weixinpay.refund(**refund_data)
    if ret.get("return_code", '') == "SUCCESS":
        receive_sign = ret.pop('sign')
        mysign = weixinpay.sign(ret)
        if receive_sign == mysign:
            ret.pop('serializer', None)

            result_model.objects.create(**ret)
            return (1000, "退款成功")
        else:
            return (4302, "退款异常")
    else:
        return (4303, ret)
