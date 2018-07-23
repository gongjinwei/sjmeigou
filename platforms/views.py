from rest_framework.views import Response, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser

from django.utils.crypto import get_random_string

# Create your views here.

from . import serializers, models
from tools.viewset import CreateOnlyViewSet


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


class StoreActivityViewSets(ModelViewSet):
    queryset = models.StoreActivityType.objects.all()
    serializer_class = serializers.StoreActivitySerializer


class DeliversViewSets(ModelViewSet):
    queryset = models.Delivers.objects.all()
    serializer_class = serializers.DeliverSerializer


class DeliverServicesViewSets(ModelViewSet):
    queryset = models.DeliverServices.objects.all()
    serializer_class = serializers.DeliverServiceSerializer
