import string

from django.db import models
from django.contrib.auth.models import User
from index.models import Application

# Create your models here.


class CheckApplication(models.Model):
    application=models.ForeignKey(to=Application,on_delete=models.CASCADE)
    checker=models.ForeignKey(to=User,on_delete=models.DO_NOTHING,editable=False)
    apply_status=models.SmallIntegerField(choices=((2,'打款验证中'),(4,'审核不通过')))
    opinion=models.CharField(max_length=255,help_text='审核意见')
    check_time=models.DateTimeField(auto_now=True,editable=False)


class CodeWarehouse(models.Model):
    application=models.OneToOneField(to=Application,on_delete=models.DO_NOTHING)
    code=models.CharField(max_length=16,editable=False,unique=True)
    use_state=models.SmallIntegerField(choices=((0,'未使用'),(1,'已使用')),editable=False)
    active_user=models.ForeignKey(to=User,editable=False,null=True,blank=True,on_delete=models.SET_NULL)
    active_time=models.DateTimeField(auto_now=True,editable=False)
    create_time=models.DateTimeField(auto_now_add=True,editable=False)


class CreateStore(models.Model):
    info=models.OneToOneField(to=Application,on_delete=models.CASCADE)
    business_hour_from=models.TimeField()
    business_hour_to=models.TimeField()



