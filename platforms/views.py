import decimal
from rest_framework.views import Response, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from django.utils.crypto import get_random_string
from rest_framework.decorators import action


# Create your views here.

from . import serializers, models
from tools.viewset import ListOnlyViewSet
from order.views import prepare_payment
from store.models import Stores
from wxpay.views import myweixinpay


class CheckApplicationViewSets(ModelViewSet):
    queryset = models.CheckApplication.objects.all()
    serializer_class = serializers.CheckApplicationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data['application']
        if application.application_status == 1:
            app_status = serializer.validated_data['apply_status']
            if app_status == 3:
                if not models.CodeWarehouse.objects.filter(application=application).exists():
                    code = get_random_string()
                    while models.CodeWarehouse.objects.filter(code=code).exists():
                        code = get_random_string()
                    models.CodeWarehouse.objects.create(application=application, code=code, use_state=0,
                                                        active_user=request.user)
                    # 发送短信给用户
                    app_status = 5
            models.Application.objects.filter(pk=application.application_id).update(application_status=app_status)
        else:
            return Response('该状态无法被更改', status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(checker=self.request.user)

    def get_queryset(self):
        if self.request.user.is_staff:
            queryset=self.queryset
        elif self.request.user.is_authenticated:
            queryset=self.queryset.filter(application__application_user=self.request.user)
        else:
            queryset=models.CheckApplication.objects.none()
        return queryset


class StoreActivityViewSets(ModelViewSet):
    queryset = models.StoreActivityType.objects.all()
    serializer_class = serializers.StoreActivitySerializer


class DeliversViewSets(ModelViewSet):
    queryset = models.Delivers.objects.all()
    serializer_class = serializers.DeliverSerializer


class DeliverServicesViewSets(ModelViewSet):
    queryset = models.DeliverServices.objects.all()
    serializer_class = serializers.DeliverServiceSerializer


class AccountRechargeViewSets(ModelViewSet):
    queryset = models.AccountRecharge.objects.filter(recharge_result=True)
    serializer_class = serializers.AccountRechargeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recharge_type=serializer.validated_data['recharge_type']
        if recharge_type ==1 and hasattr(request.user,'stores'):
            account,created = models.Account.objects.get_or_create(user=None,store=request.user.stores,account_type=5)
        elif recharge_type ==2 and request.user.is_staff:
            account,created = models.Account.objects.get_or_create(user=None,store=None,account_type=4)
        else:
            return Response('你无此充值权限',status=status.HTTP_400_BAD_REQUEST)
        recharge=serializer.save(account=account)
        ret=prepare_payment(request.user,recharge.recharge_desc,recharge.recharge_money,recharge.id,'recharge')
        return Response(ret, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        queryset = self.queryset
        if not (self.request.user.is_authenticated and hasattr(self.request.user,'stores')):
            return queryset.none()
        elif self.request.user.is_staff:
            return queryset
        else:
            return queryset.filter(account__store=self.request.user.stores)


class AccountViewSets(ModelViewSet):
    queryset = models.Account.objects.all()
    serializer_class = serializers.AccountSerializer

    def get_queryset(self):
        queryset=self.queryset
        store_id = self.request.query_params.get('store','')
        if store_id:
            try:
                store_id=int(store_id)
                if Stores.objects.filter(pk=store_id).exists():
                    store = Stores.objects.get(pk=store_id)
                    return queryset.filter(store=store)
                else:
                    return queryset.none()
            except ValueError:
                return queryset.none()
        elif self.request.user.is_staff:
            return queryset
        elif hasattr(self.request,'user') and self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
        else:
            return queryset.none()

    @action(methods=['get','post'],detail=False,serializer_class=serializers.BankCardSerializer)
    def bank_card(self,request):
        if hasattr(request,'user') and request.user.is_authenticated:
            if request.method == 'GET':
                queryset = models.BankCard.objects.filter(user=request.user)
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    return self.get_paginated_response(serializer.data)

                serializer = self.get_serializer(queryset, many=True)
                return Response(serializer.data)
            elif request.method == 'POST':
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)

                serializer.save(user=request.user)
                return Response(serializer.data)
        else:
            return Response('请先登录')

    @action(methods=['get','post'],detail=True,serializer_class=serializers.TolingqiangSerializer)
    def to_lingqian(self,request,pk=None):
        obj = self.get_object()
        if request.method =='GET':
            queryset = models.BankNo.objects.all()
            bank_no_serializer = serializers.BankNoSerializer(queryset,many=True)
            return Response(bank_no_serializer.data)
        elif request.method == 'POST':
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            amount = serializer.validated_data['amount']
            if obj.account_type==5:
                return Response({"result_code": "FAIL","err_code_des":'物流账户不可提现'})
            elif obj.account_type ==3 and amount>=100 and amount<=int(obj.bank_balance*100):
                data ={
                    'openid':request.user.userinfo.openId,
                    'amount':amount,
                    'desc':'转至微信零钱',
                    'spbill_create_ip':request.META['HTTP_X_FORWARDED_FOR'] if 'HTTP_X_FORWARDED_FOR' in request.META else request.META['REMOTE_ADDR']
                }
                r=myweixinpay.to_lingqiang(**data)
                result_code = r.get('result_code','FAIL')
                return_code = r.get('return_code','FAIL')
                if result_code =='SUCCESS' and return_code=='SUCCESS':
                    serializer.save(partner_trade_no=r['partner_trade_no'],to_user=request.user,payment_no=r['payment_no'],payment_time=r['payment_time'])
                    obj.bank_balance -=decimal.Decimal(amount/100)
                    obj.save()
                return Response(r)
            else:
                return Response({"result_code": "FAIL","err_code_des":'金额不能少于1元，提现金额不能大于余额'})


class DeliveryReasonView(ModelViewSet):
    queryset = models.DeliveryReason.objects.all()
    serializer_class = serializers.DeliverReasonSerializer
    filter_backends = (DjangoFilterBackend,OrderingFilter)
    filter_fields=('reason_type',)
    ordering_fields=('id',)


class ProtocolViewSets(ModelViewSet):
    queryset = models.Protocol.objects.all()
    serializer_class = serializers.ProtocolSerializer


class RefundReasonViewSets(ModelViewSet):
    queryset = models.RefundReason.objects.all()
    serializer_class = serializers.RefundReasonSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_fields = ('reason_type',)
    ordering_fields = ('id',)


class BargainPosterViewSets(ModelViewSet):
    queryset = models.BargainPoster.objects.all()
    serializer_class = serializers.BargainPosterSerializer
