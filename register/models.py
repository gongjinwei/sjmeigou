from django.db import models
import datetime

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

    def __str__(self):
        return self.nickName

class Image(models.Model):
    image=models.ImageField(upload_to='sjmeigou/%Y%m%d',max_length=256)
