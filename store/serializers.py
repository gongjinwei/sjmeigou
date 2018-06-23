# -*- coding:UTF-8 -*-
from rest_framework import serializers
from . import models




class CheckApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CheckApplication
        fields = '__all__'

