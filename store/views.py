from rest_framework.views import Response,status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser

from django.utils.crypto import get_random_string

from register.viewset import CreateOnlyViewSet

# Create your views here.

from . import serializers,models


class CheckApplicationViewSets(ModelViewSet):
    queryset = models.CheckApplication.objects.all()
    serializer_class = serializers.CheckApplicationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application=serializer.validated_data['application']
        if application.application_status==1:
            application.application_status=serializer.validated_data['apply_status']
            application.save()
        else:
            return Response('该状态无法被更改',status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class GenerateCodeView(CreateOnlyViewSet):
    queryset = models.CodeWarehouse.objects.all()
    serializer_class = serializers.GenerateCodeSerializer
    permission_classes = (IsAdminUser,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        generate=serializer.validated_data.get('generate',False)
        if generate:
            data={
                "code":get_random_string(),
                "use_state":0,
                "active_user":request.user
            }
            serializer.validated_data.update(data)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response('请设置generate为true',status=status.HTTP_400_BAD_REQUEST)