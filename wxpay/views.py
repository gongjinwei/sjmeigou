import time, copy
from django.conf import settings
from rest_framework.views import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from datetime import datetime
from django.db.models import F

from tools import viewset

from weixin.pay import WeixinPay

from . import serializers,models
from register.views import CustomerXMLRender,CustomerXMLParser
from order.models import StoreOrder,UnifyOrder,JoinActivity,OrderTrade

# Create your views here.
mch_id = getattr(settings, "WEIXIN_MCH_ID")
mch_key = getattr(settings, "WEIXIN_MCH_KEY")
notify_url = getattr(settings, "WEIXIN_NOTIFY_URL")
mch_key_file = getattr(settings, "WEIXIN_MCH_KEY_FILE")
mch_cert_file = getattr(settings, "WEIXIN_MCH_CERT_FILE")
app_id = getattr(settings, "APPID")
app_secret = getattr(settings, "APPSECRET")


weixinpay = WeixinPay(app_id, mch_id, mch_key, notify_url)


class NotifyOrderView(viewset.CreateOnlyViewSet):
    serializer_class = serializers.NotifyOrderSerializer
    queryset = models.NotifyOrderModel.objects.all()
    permission_classes = (AllowAny,)
    renderer_classes = (CustomerXMLRender,)
    parser_classes = (CustomerXMLParser,)

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data=copy.copy(serializer.validated_data)
        received_sign=data.pop('sign','')
        # 重复使用签名验证
        # if models.NotifyOrderModel.objects.filter(sign=received_sign).exists():
        #     return Response({"return_code":"False","return_msg":"exists error"})
        sign=weixinpay.sign(data)
        if received_sign==sign:
            return_code = data.get('return_code')
            fee_type = data.get('fee_type')
            if return_code =='SUCCESS' and fee_type=='CNY':
                cash_fee = data.get('cash_fee',0)/100
                out_trade_no = data.get('out_trade_no')
                time_end = data.get('time_end')
                paid_time = datetime.strptime(time_end,'%Y%m%d%H%M%S')
                if OrderTrade.objects.filter(pk=out_trade_no).exists():
                    order_trade=OrderTrade.objects.get(pk=out_trade_no)
                    order_trade.paid_time=paid_time
                    order_trade.paid_money=Decimal(cash_fee)
                    order_trade.save()
                    if order_trade.unify_order:
                        order=order_trade.unify_order
                        self.receive_fee(order,cash_fee,paid_time)
                    elif order_trade.store_order:
                        order=order_trade.store_order
                        self.receive_fee(order, cash_fee, paid_time)
                        # 减优惠券
                        if order.coupon:
                            order.coupon.has_num-=1
                            order.coupon.save()
                        # 参加活动一次
                        if order.activity:
                            join_act,created=JoinActivity.objects.get_or_create(defaults=dict(user=order.user,activity=order.activity,nums_join=1),user=order.user,activity=order.activity)
                            if not created:
                                join_act.nums_join+=1
                                join_act.save()
                        # 减库存
                        if hasattr(order,'sku_orders'):
                            for sku_data in order.sku_orders.all():
                                sku_data.sku.stock-=sku_data.num
                                sku_data.sku.save()
                    elif order_trade.recharge:
                        recharge = order_trade.recharge
                        recharge.recharge_result=True
                        # 余额增加
                        recharge.account.bank_balance+=Decimal(cash_fee)
                        recharge.account.save()
                        recharge.save()

            self.perform_create(serializer)
            return Response({"return_code":"SUCCESS","return_msg":"OK"})
        else:
            return Response({"return_code":"False","return_msg":"sign error"})

    @staticmethod
    def receive_fee(order,cash_fee,paid_time):
        order.account_paid = cash_fee
        order.paid_time = paid_time
        if order.account <= order.account_paid:
            order.state=2

            # 发物流订单
            if hasattr(order, 'store_orders'):
                order.store_orders.update(account_paid=F('account'),state=2)
        if hasattr(order,'unify_order'):
            relate_order=order.unify_order
            relate_order.account_paid+=Decimal(cash_fee)
            relate_order.paid_time=paid_time
            if relate_order.account <= relate_order.account_paid:
                relate_order.state=2
            relate_order.save()

        order.save()