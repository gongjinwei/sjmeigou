# -*- coding:UTF-8 -*-
from rest_framework import serializers
import re

from . import models


def mobile_validator(value):
    matcher = re.match('^13[0-9]|14[579]|15[0-3,5-9]|16[6]|17[0135678]|18[0-3,5-9]|19[89]\\d{8}$', value)
    if not matcher:
        raise serializers.ValidationError('手机号码不正确')


def code_validator(value):
    matcher = re.match(r'^\d{6}$', value)
    if not matcher:
        raise serializers.ValidationError('验证码不正确')


class CheckSerializer(serializers.Serializer):
    mobile = serializers.CharField(required=True, validators=[mobile_validator],
                                   help_text='11位手机号，作为用户名登录。必须符号手机号规则')
    code = serializers.CharField(required=True, validators=[code_validator], help_text='6位数字短信验证码')

    userId = serializers.CharField(required=True, max_length=32, help_text="上传userId")


class SendSerializer(serializers.Serializer):
    mobile = serializers.CharField(required=True, validators=[mobile_validator],
                                   help_text='11位手机号，作为用户名登录。必须符号手机号规则')


class GetUserInfoSerializer(serializers.Serializer):
    js_code = serializers.CharField(max_length=50, required=True)
    encrypted_data = serializers.CharField(max_length=1000, required=True)
    iv = serializers.CharField(max_length=50, required=True)

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.Image
        fields='__all__'


class VodCallbackSerializer(serializers.ModelSerializer):
    data = serializers.JSONField()

    class Meta:
        model=models.VodCallback
        fields='__all__'
