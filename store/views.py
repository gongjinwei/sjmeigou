from rest_framework.views import Response
from rest_framework.viewsets import ModelViewSet

# Create your views here.

from . import serializers,models


class CheckApplicationViewSets(ModelViewSet):
    queryset = models.CheckApplication
    serializer_class = serializers.CheckApplicationSerializer

