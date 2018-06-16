# -*- coding:UTF-8 -*-

from rest_framework import serializers
from . import models


class OrderCallbackSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.OrderCallback
        fields='__all__'