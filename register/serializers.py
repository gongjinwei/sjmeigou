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
        exclude = ('id',)


class VideoStreamSerializer(serializers.ModelSerializer):

    class Meta:
        model=models.VideoStream
        exclude = ('id',)


class AudioStreamSerializer(serializers.ModelSerializer):

    class Meta:
        model=models.AudioStream
        exclude = ('id',)


class MetaDataSerializer(serializers.ModelSerializer):
    videoStreamList=VideoStreamSerializer(many=True)
    audioStreamList=AudioStreamSerializer(many=True)

    class Meta:
        model=models.VodMetaData
        exclude = ('id',)

    def create(self, validated_data):
        video_stream_list=validated_data.pop('videoStreamList')
        audio_stream_list=validated_data.pop('audioStreamList')
        meta_data=models.VodMetaData.objects.create(**validated_data)

        for video_stream in video_stream_list:
            models.VideoStream.objects.create(metaData_id=meta_data.id,**video_stream)
        for audio_stream in audio_stream_list:
            models.AudioStream.objects.create(metaData_id=meta_data.id,**audio_stream)

        return meta_data


class VodDataSerializer(serializers.ModelSerializer):
    metaData=MetaDataSerializer()

    class Meta:
        model=models.VodData
        exclude=('id',)

    def create(self, validated_data):
        meta_data=validated_data.pop('metaData')
        vod_data=models.VodData.objects.create(**validated_data)
        meta_data.update(vodData_id=vod_data.id)
        MetaDataSerializer().create(meta_data)

        return vod_data


class VodCallbackSerializer(serializers.ModelSerializer):
    data = VodDataSerializer()

    class Meta:
        model=models.VodCallback
        exclude = ('id',)

    def create(self, validated_data):
        vod_data=validated_data.pop('data')
        vod_callback=models.VodCallback.objects.create(**validated_data)
        vod_data.update(callback_id=vod_callback.id)
        VodDataSerializer().create(vod_data)

        return vod_callback


class GetVodSignatureSerializer(serializers.Serializer):
    sourceContext=serializers.CharField(max_length=50,required=True)
    videoSize=serializers.IntegerField(max_value=20971520)

