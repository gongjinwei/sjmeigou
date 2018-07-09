from rest_framework.views import Response, status
from rest_framework.viewsets import ModelViewSet

# Create your views here.

from . import serializers, models


class CheckApplicationViewSets(ModelViewSet):
    queryset = models.CheckApplication.objects.all()
    serializer_class = serializers.CheckApplicationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data['application']
        if application.application_status == 1:
            application.application_status = serializer.validated_data['apply_status']
            application.save()
        else:
            return Response('该状态无法被更改', status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class StoreActivityViewSets(ModelViewSet):
    queryset = serializers.StoreActivityType.objects.all()
    serializer_class = serializers.StoreActivitySerializer