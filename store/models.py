import string

from django.db import models
from django.contrib.auth.models import User
from index.models import Application

# Create your models here.


store_deposit=1000


class CodeWarehouse(models.Model):
    application=models.OneToOneField(to=Application,on_delete=models.DO_NOTHING)
    code=models.CharField(max_length=16,editable=False,unique=True)
    use_state=models.SmallIntegerField(choices=((0,'未使用'),(1,'已使用')),editable=False)
    active_user=models.ForeignKey(to=User,editable=False,null=True,blank=True,on_delete=models.SET_NULL)
    active_time=models.DateTimeField(auto_now=True,editable=False)
    create_time=models.DateTimeField(auto_now_add=True,editable=False)


class Stores(models.Model):
    info=models.OneToOneField(to=Application,on_delete=models.CASCADE)
    active_code=models.CharField(max_length=20,default='')
    business_hour_from=models.TimeField()
    business_hour_to=models.TimeField()
    active_state=models.BooleanField(default=False,editable=False)
    user=models.OneToOneField(to=User,editable=False,on_delete=models.CASCADE)
    create_time=models.DateTimeField(auto_now_add=True,editable=False)
    update_time=models.DateTimeField(auto_now=True,editable=False)


class Deposit(models.Model):
    application=models.OneToOneField(to=Application,on_delete=models.DO_NOTHING)
    put_in_time=models.DateTimeField(auto_now_add=True,editable=False)
    deposit=models.IntegerField(default=store_deposit,editable=False)
    deposit_desc=models.CharField(default='保证金',max_length=255,editable=False)
    has_paid=models.BooleanField(default=False,editable=False)
    has_paid_money=models.IntegerField(default=0,editable=False)
    success_paid_time=models.DateTimeField(editable=False,blank=True,null=True)






