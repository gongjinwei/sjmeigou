from rest_framework.viewsets import ModelViewSet
from rest_framework.views import Response,status
from rest_framework.permissions import AllowAny

# Create your views here.
from . import models,serializers


class OrderCallbackViewSets(ModelViewSet):
    serializer_class = serializers.OrderCallbackSerializer
    queryset = models.OrderCallback.objects.all()
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({'success':True}, status=status.HTTP_200_OK, headers=headers)

