# -*- coding:UTF-8 -*-
import time,json
import hashlib
import requests


class DianWoDa:
    def __init__(self, pk, secret, url, fmt='json'):
        self.pk = pk
        self.secret = secret
        self.format = fmt
        self.url = url

    def sig(self, params):
        B = self.secret + ''.join(['%s%s' % (k, params[k]) for k in sorted(params.keys())]) + self.secret

        return hashlib.sha1(B.encode()).hexdigest().upper()

    def _send_prepare(self, url_postfix, method='POST', **params):
        url = self.url + url_postfix
        tmp_dict = {
            'pk': self.pk,
            'timestamp': int(time.time() * 1000),
            'format': self.format,
            'sig': self.sig(params)
        }
        tmp_dict.update(**params)
        r = requests.request(method, url=url, data=tmp_dict)
        return r.json()

    # 派发订单
    def order_send(self, params):
        url_postfix = '/api/v3/order-send.json'
        r = self._send_prepare(url_postfix, **params)
        return r

    # 接受订单测试

    def order_accept_test(self, order_original_id):
        url_postfix = '/api/v3/order-accepted-test.json'
        r = self._send_prepare(url_postfix, order_original_id=order_original_id)
        print(r)

    # 完成到店测试

    def order_arrive_test(self, order_original_id):
        url_postfix = '/api/v3/order-arrive-test.json'
        r = self._send_prepare(url_postfix, order_original_id=order_original_id)
        print(r)

    # 完成取货测试
    def order_fetch_test(self, order_original_id):
        url_postfix = '/api/v3/order-fetch-test.json'
        r = self._send_prepare(url_postfix, order_original_id=order_original_id)
        print(r)

    # 完成配送测试
    def order_finish_test(self, order_original_id):
        url_postfix = '/api/v3/order-finish-test.json'
        r = self._send_prepare(url_postfix, order_original_id=order_original_id)
        print(r)

    # 获取订单信息
    def order_get(self, order_original_id):
        url_postfix = '/api/v3/order-get.json'
        r = self._send_prepare(url_postfix, order_original_id=order_original_id)
        return r

    # 取消订单
    def order_cancel(self, order_original_id, cancel_reason):
        url_postfix = '/api/v3/order-cancel.json'
        r = self._send_prepare(url_postfix, order_original_id=order_original_id, cancle_reason=cancel_reason)
        print(r)

    # 修改订单备注

    def order_update_remark(self, order_original_id, order_info_content):
        url_postfix = '/api/v3/order-update-remark.json'
        r = self._send_prepare(url_postfix, order_original_id=order_original_id, order_info_content=order_info_content)
        print(r)

    # 获取配送员位置信息

    def order_rider_position(self, order_original_id, rider_code):
        url_postfix = '/api/v3/order-rider-position.json'
        r = self._send_prepare(url_postfix, order_original_id=order_original_id, rider_code=rider_code)
        print(r)

    # 查询订单应收商家费用

    def order_receivable_price(self, order_original_id):
        url_postfix = '/api/v3/order-receivable-price.json'
        r = self._send_prepare(url_postfix=url_postfix, order_original_id=order_original_id)
        print(r)

    # 创建商家/站点/寄件人

    def save_shops(self, shops_list):
        if isinstance(shops_list,list):
            shops_list=json.dumps(shops_list)
        url_postfix = '/api/v3/batchsave-store.json'
        r = self._send_prepare(url_postfix=url_postfix, shops=shops_list)
        print(r)


# x = DianWoDa(DWD_APPKEY, DWD_SECRET, DWD_TEST_URL)

# x.order_send(tmp_json)
# x.order_cancel('JFWL2018061507','不要了')
# x.order_get('JFWL2018061507')
# x.order_accept_test('JFWL2018061506')
# x.order_rider_position('JFWL2018061503','30398')
# x.order_arrive_test('JFWL2018061507')
# x.order_fetch_test('JFWL2018061507')
# x.order_finish_test('JFWL2018061507')
# x.order_receivable_price('JFWL2018061503')
# shops_list = [
#     {"addr": "长宁区长宁路820号",
#      "city_code": "110100",
#      "external_shopid": "3728970",
#      "lat": 31218268,
#      "lng": 121417321,
#      "mobile": "18101944465",
#      "shop_title": "南洋茶铺"}]
#
# x.save_shops(shops_list)
