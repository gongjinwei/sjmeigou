import time, copy
from django.conf import settings
from rest_framework.views import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from datetime import datetime
from django.db.models import F

from tools import viewset, dianwoda

from weixin.pay import WeixinPay

from . import serializers, models
from register.views import CustomerXMLRender, CustomerXMLParser
from order.models import JoinActivity, OrderTrade, DwdOrder
from platforms.models import Account, KeepAccounts
from platforms.serializers import KeepAccountSerializer

# Create your views here.
mch_id = getattr(settings, "WEIXIN_MCH_ID")
mch_key = getattr(settings, "WEIXIN_MCH_KEY")
notify_url = getattr(settings, "WEIXIN_NOTIFY_URL")
mch_key_file = getattr(settings, "WEIXIN_MCH_KEY_FILE")
mch_cert_file = getattr(settings, "WEIXIN_MCH_CERT_FILE")
app_id = getattr(settings, "APPID")
app_secret = getattr(settings, "APPSECRET")
DWD_SECRET = getattr(settings, 'DWD_SECRET')
DWD_APPKEY = getattr(settings, 'DWD_APPKEY')
DWD_TEST_URL = getattr(settings, 'DWD_TEST_URL')
DWD_ORIGINAL_URL = getattr(settings, 'DWD_ORIGINAL_URL')

weixinpay = WeixinPay(app_id, mch_id, mch_key, notify_url)
dwd = dianwoda.DianWoDa(DWD_APPKEY, DWD_SECRET, DWD_TEST_URL)


class NotifyOrderView(viewset.CreateOnlyViewSet):
    serializer_class = serializers.NotifyOrderSerializer
    queryset = models.NotifyOrderModel.objects.all()
    permission_classes = (AllowAny,)
    renderer_classes = (CustomerXMLRender,)
    parser_classes = (CustomerXMLParser,)

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = copy.copy(serializer.validated_data)
        received_sign = data.pop('sign', '')
        # 重复使用签名验证
        # if models.NotifyOrderModel.objects.filter(sign=received_sign).exists():
        #     return Response({"return_code":"False","return_msg":"exists error"})
        sign = weixinpay.sign(data)
        if received_sign == sign:
            return_code = data.get('return_code')
            fee_type = data.get('fee_type')
            # 取平台账号
            platform_account, created = Account.objects.get_or_create(user=None, store=None, account_type=1)

            if return_code == 'SUCCESS' and fee_type == 'CNY':
                cash_fee = Decimal(data.get('cash_fee', 0) / 100)
                out_trade_no = data.get('out_trade_no')
                time_end = data.get('time_end')
                paid_time = datetime.strptime(time_end, '%Y%m%d%H%M%S')
                if OrderTrade.objects.filter(pk=out_trade_no).exists():

                    # 把交易时间与交易金额写入交易中
                    order_trade = OrderTrade.objects.get(pk=out_trade_no)
                    order_trade.paid_time = paid_time
                    order_trade.paid_money = cash_fee
                    order_trade.save()

                    # 处理平台付款
                    if order_trade.unify_order:
                        order = order_trade.unify_order
                        self.receive_fee(order, cash_fee, paid_time, platform_account)

                    # 处理店铺订单付款
                    elif order_trade.store_order:
                        order = order_trade.store_order
                        self.receive_fee(order, cash_fee, paid_time, platform_account)
                        # 减优惠券
                        if order.coupon:
                            order.coupon.has_num -= 1
                            order.coupon.save()
                        # 参加活动一次
                        if order.activity:
                            join_act, created = JoinActivity.objects.get_or_create(
                                defaults=dict(user=order.user, activity=order.activity, nums_join=1), user=order.user,
                                activity=order.activity)
                            if not created:
                                join_act.nums_join += 1
                                join_act.save()
                        # 减库存
                        if hasattr(order, 'sku_orders'):
                            for sku_data in order.sku_orders.all():
                                sku_data.sku.stock -= sku_data.num
                                sku_data.sku.save()

                    # 处理充值
                    elif order_trade.recharge:
                        recharge = order_trade.recharge
                        recharge.recharge_result = True
                        recharge.paid_money = cash_fee
                        # 余额增加且平台账户增加收入
                        recharge.account.bank_balance += cash_fee
                        platform_account.bank_balance += cash_fee
                        # 记录平台收入一笔

                        keep_data = {
                            "voucher": 1,
                            "money": cash_fee * 100,
                            "remark": '%s充值收入' % recharge.account.get_account_type_display(),
                            "intercourse_business2": recharge.id,
                            'account': recharge.account.id,
                            'keep_account_no': KeepAccounts.account_no()
                        }
                        keep_serializer = KeepAccountSerializer(data=keep_data)
                        keep_serializer.is_valid(raise_exception=True)
                        keep_serializer.save()
                        recharge.account.save()
                        recharge.save()

            self.perform_create(serializer)
            return Response({"return_code": "SUCCESS", "return_msg": "OK"})
        else:
            return Response({"return_code": "False", "return_msg": "sign error"})

    def receive_fee(self, order, cash_fee, paid_time, plat_account):
        order.account_paid = cash_fee

        order.paid_time = paid_time
        if order.account <= cash_fee:
            order.state = 2

            # 处理合并支付成功
            if hasattr(order, 'store_orders'):

                order.store_orders.update(account_paid=F('account'), state=2, paid_time=paid_time)
                # 下物流单
                for store_o in order.store_orders:
                    self.order_deliver_server(store_o, plat_account)
            else:
                # 没有店铺订单，平台收入增加
                plat_account.bank_balance += cash_fee
                plat_account.save()
                # 记一笔平台收入
                keep_data = {
                    "voucher": 1,
                    "money": cash_fee * 100,
                    "remark": '平台其他收入',
                    'account': plat_account.id,
                    'keep_account_no': KeepAccounts.account_no()
                }
                keep_serializer = KeepAccountSerializer(data=keep_data)
                keep_serializer.is_valid(raise_exception=True)
                keep_serializer.save()

        # 处理店铺单独付款订单-平台连锁单
        if hasattr(order, 'unify_order'):
            # 下物流单
            self.order_deliver_server(order, plat_account)

            relate_order = order.unify_order
            relate_order.account_paid += cash_fee
            relate_order.paid_time = paid_time
            if relate_order.account <= relate_order.account_paid:
                relate_order.state = 2
            relate_order.save()

        order.save()

    def order_deliver_server(self, store_order, plat_account):
        if store_order.store_to_pay > Decimal(0.00):
            # 取出店铺物流账户,分别作余额扣减
            store_account = Account.objects.get(user=None, store=store_order.store, account_type=5)
            plat_account.bank_balance -= store_order.deliver_payment
            store_account.bank_balance -= store_order.store_to_pay

            self.send_store_deliver(store_order)
            # 发起物流单

    def send_store_deliver(self, store_order):
        store = store_order.store
        receive_address = store_order.unify_order.address
        tmp_json = {
            'order_original_id': store_order.store_order_no,
            'order_create_time': int(store_order.paid_time.timestamp() * 1000),
            'order_remark': '',
            'order_price': int(store_order.account_paid * 100),
            'cargo_weight': 0,
            'cargo_num': 1,
            'city_code': '330100',
            'seller_id': str(store.id),
            'seller_name': store.info.contract_name,
            'seller_mobile': store.info.contract_mobile,
            'seller_address': store.receive_address,
            'seller_lat': store.latitude,
            'seller_lng': store.longitude,
            'consignee_name': receive_address.contact,
            'consignee_mobile': receive_address.phone,
            'consignee_address': receive_address.address + receive_address.room_no,
            'consignee_lat': round(receive_address.latitude, 6),
            'consignee_lng': round(receive_address.longitude, 6),
            'money_rider_needpaid': 0,
            'money_rider_prepaid': 0,
            'money_rider_charge': 0,
            'time_waiting_at_seller': 300,
            'delivery_fee_from_seller': 0
        }

        ret = dwd.order_send(tmp_json)
        if ret.get('errorCode', '') == '0':
            dwd_order_id = ret['result']['dwd_order_id']
            dwd_order_distance = ret['result']['distance']
            DwdOrder.objects.create(store_order=store_order, dwd_order_id=dwd_order_id,
                                    dwd_order_distance=dwd_order_distance)
