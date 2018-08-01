# -*- coding:UTF-8 -*-

from rest_framework import serializers
from . import models

from wxpay.views import dwd


class OrderCallbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrderCallback
        fields = '__all__'


class InitDwdOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InitDwdOrder
        fields = ('store_order', 'create_time')

    def create(self, validated_data):
        request = self.context.get('request')
        op = request.query_params.get('op', '')
        store_order = validated_data['store_order']
        receive_address = store_order.unify_order.address
        store = store_order.store
        dwdorder=models.InitDwdOrder()
        temp = {
            'order_original_id': dwdorder.trade_number,
            'order_create_time': int(store_order.paid_time.timestamp() * 1000),
            'order_remark': '',
            'order_price': int(store_order.account_paid * 100),
            'cargo_weight': 0,
            'cargo_num': 1,
            'city_code': store.adcode,
            'seller_id': request.user.userInfo.openId,
            'money_rider_needpaid': 0,
            'money_rider_prepaid': 0,
            'money_rider_charge': 0,
            'time_waiting_at_seller': 300,
            'delivery_fee_from_seller': 0
        }
        if op == 'backend' and hasattr(request.user, 'stores') and store_order.store == request.user.stores:
            temp.update({
                'seller_name': store.info.contract_name,
                'seller_mobile': store.info.contract_mobile,
                'seller_address': store.receive_address,
                'seller_lat': store.latitude,
                'seller_lng': store.longitude,
                'consignee_name': receive_address.contact,
                'consignee_mobile': receive_address.phone,
                'consignee_address': receive_address.address + receive_address.room_no,
                'consignee_lat': round(receive_address.latitude, 6),
                'consignee_lng': round(receive_address.longitude, 6)
            })

        elif op !='backend' and store_order.user == request.user:
            temp.update({
                'seller_name': receive_address.contact,
                'seller_mobile': receive_address.phone,
                'seller_address': receive_address.address + receive_address.room_no,
                'seller_lat': round(receive_address.latitude, 6),
                'seller_lng': round(receive_address.longitude, 6),
                'consignee_name': store.info.contract_name,
                'consignee_mobile': store.info.contract_mobile,
                'consignee_address': store.receive_address,
                'consignee_lat': store.latitude,
                'consignee_lng': store.longitude
            })
        dwd.order_send(**temp)