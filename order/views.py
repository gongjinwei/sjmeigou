from rest_framework.views import Response,status
from rest_framework.viewsets import ModelViewSet


# Create your views here.

from . import serializers,models

class ShoppingCarView(ModelViewSet):
    serializer_class = serializers.ShoppingCarItemSerializer

    def get_queryset(self):
        queryset=models.ShoppingCarItem.objects.filter(user=self.request.user)

        return queryset

