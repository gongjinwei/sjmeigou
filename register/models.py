from django.db import models
import datetime
from jsonfield import JSONField

from django.contrib.auth.models import User


# Create your models here.


class UserInfo(models.Model):
    id = models.CharField(help_text='用户小程序ID', primary_key=True, editable=False, max_length=50)
    openId = models.CharField(help_text='用户公开ID', max_length=100, default='')
    avatarUrl = models.CharField(max_length=255, default='')
    city = models.CharField(max_length=100, default='')
    gender = models.SmallIntegerField(default=1)
    language = models.CharField(max_length=50, default='')
    nickName = models.CharField(max_length=100, default='')
    province = models.CharField(max_length=100, default='')
    country = models.CharField(max_length=100, default='')
    createTime = models.DateTimeField(auto_now_add=True, editable=False)
    user=models.OneToOneField(to=User,on_delete=models.DO_NOTHING,blank=True,null=True)

    def __str__(self):
        return self.nickName


class Image(models.Model):
    image = models.ImageField(upload_to='sjmeigou/%Y%m%d', max_length=256)


class VodCallback(models.Model):
    version = models.CharField(max_length=10, default='', blank=True)
    eventType = models.CharField(max_length=100, default='', blank=True)


class VodData(models.Model):
    callback = models.OneToOneField(to='VodCallback', on_delete=models.DO_NOTHING, related_name='data', editable=False)
    status = models.IntegerField(default=0)
    message = models.CharField(max_length=255, default="", blank=True)
    vodTaskId = models.CharField(max_length=100, default="", blank=True)
    fileId = models.CharField(max_length=50, default="", blank=True)
    fileUrl = models.CharField(max_length=255, default="", blank=True)
    continued = models.IntegerField(default=0)
    author = models.CharField(max_length=100, default='', blank=True)
    streamId = models.CharField(max_length=100, default="", blank=True)
    sourceType = models.CharField(max_length=100, default="", blank=True)
    sourceContext = models.CharField(max_length=100, default="", blank=True)


class VodMetaData(models.Model):
    vodData = models.OneToOneField(to='VodData', on_delete=models.CASCADE, related_name='metaData', editable=False)
    height = models.IntegerField(default=360)
    width = models.IntegerField(default=540)
    bitrate = models.IntegerField(default=916924)
    size = models.IntegerField(default=0)
    container = models.CharField(default="mov,mp4,m4a,3gp,3g2,mj2", max_length=50, blank=True)
    md5 = models.CharField(default="", max_length=30, blank=True)
    duration = models.IntegerField(default=0)
    floatDuration = models.FloatField(default=0.0)
    totalSize = models.IntegerField(default=0)
    rotate = models.IntegerField(default=0)


class VideoStream(models.Model):
    metaData = models.ForeignKey(to='VodMetaData', on_delete=models.DO_NOTHING, related_name='videoStreamList',
                                 editable=False)
    bitrate = models.IntegerField(default=788426)
    height = models.IntegerField(default=360)
    width = models.IntegerField(default=640)
    codec = models.CharField(max_length=30, default='mpeg4', blank=True)
    fps = models.IntegerField(default=23)


class AudioStream(models.Model):
    metaData = models.ForeignKey(to='VodMetaData', on_delete=models.DO_NOTHING, related_name='audioStreamList',
                                 editable=False)
    samplingRate = models.IntegerField(default=44100)
    bitrate = models.IntegerField(default=128498)
    codec = models.CharField(default='aac', max_length=30, blank=True)


class ReceiveMsg(models.Model):
    ToUserName = models.CharField(max_length=50)
    FromUserName = models.CharField(max_length=50)
    CreateTime = models.IntegerField()
    MsgType = models.CharField(max_length=30)
    MsgId = models.BigIntegerField()
    Content = models.CharField(max_length=255, default='', blank=True)
    PicUrl = models.CharField(max_length=128, default='', blank=True)
    MediaId = models.CharField(max_length=100, default='', blank=True)
    Title = models.CharField(max_length=100, default='', blank=True)
    Appid = models.CharField(max_length=50, default='', blank=True)
    PagePath = models.CharField(max_length=128, default='', blank=True)
    ThumbUrl = models.CharField(max_length=255, default='', blank=True)
    ThumbMediaId = models.CharField(max_length=50, default='', blank=True)
    Event = models.CharField(max_length=30, default='', blank=True)
    SessionFrom = models.CharField(max_length=100, default='', blank=True)