# -*- coding:UTF-8 -*-
from rest_framework import serializers
from . import models


class NotifyOrderSerializer(serializers.ModelSerializer):

    class Meta:
        fields="__all__"
        model=models.NotifyOrderModel
