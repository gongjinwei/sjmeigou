from rest_framework.views import Response, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser

from django.utils.crypto import get_random_string

# Create your views here.

from . import serializers, models
from tools.viewset import CreateOnlyViewSet
from order.views import prepare_payment
from store.models import Stores


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
    queryset = models.AccountRecharge.objects.all()
    serializer_class = serializers.AccountRechargeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recharge_type=serializer.validated_data['recharge_type']
        if recharge_type ==1 and hasattr(request.user,'stores') and models.Account.objects.filter(user=None,store=request.user.stores,account_type=3).exists():
            account = models.Account.objects.get(user=None,store=request.user.stores,account_type=3)
        elif recharge_type ==2 and request.user.is_staff:
            account = models.Account.objects.get(user=None,store=None,account_type=4)
        else:
            return Response('你无此充值权限',status=status.HTTP_400_BAD_REQUEST)
        recharge=serializer.save(account=account)
        ret=prepare_payment(request.user,recharge.recharge_desc,recharge.recharge_money,recharge.id,'recharge')
        return Response(ret, status=status.HTTP_201_CREATED)


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
            except ValueError:
                pass
        elif self.request.user.is_staff:
            return queryset
        else:
            return queryset.filter(user=self.request.user)