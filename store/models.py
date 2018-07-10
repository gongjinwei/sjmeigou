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
    logo=models.URLField(default='https://image.sjmeigou.com/sjmeigou/20180707/0f8c068938abc703a1604a1aa4.jpg')
    receive_address=models.CharField(null=True,max_length=128)
    longitude = models.FloatField(null=True)
    latitude = models.FloatField(null=True)
    active_state=models.SmallIntegerField(default=0,editable=False)
    user=models.OneToOneField(to=User,editable=False,on_delete=models.CASCADE)
    create_time=models.DateTimeField(auto_now_add=True,editable=False)
    update_time=models.DateTimeField(auto_now=True,editable=False)

    def __str__(self):
        return self.info.store_name


class Deposit(models.Model):
    application=models.OneToOneField(to=Application,on_delete=models.DO_NOTHING)
    put_in_time=models.DateTimeField(auto_now=True,editable=False)
    deposit=models.IntegerField(default=store_deposit,editable=False)
    deposit_desc=models.CharField(default='保证金',max_length=255,editable=False)
    has_paid=models.BooleanField(default=False,editable=False)
    has_paid_money=models.IntegerField(default=0,editable=False)
    success_paid_time=models.DateTimeField(editable=False,blank=True,null=True)


class StoreQRCode(models.Model):
    store=models.ForeignKey(to='Stores',on_delete=models.CASCADE)
    path=models.CharField(max_length=255)
    width=models.IntegerField(default=430)
    QRCodeImage=models.ImageField(upload_to='sjmeigou/stores/QRcode',null=True,blank=True,editable=False)
    create_time=models.DateTimeField(auto_now_add=True)


class GoodsType(models.Model):
    store_goods_type=models.ForeignKey(to='StoreGoodsType',on_delete=models.CASCADE,related_name='good_types')
    name = models.CharField(max_length=10)
    order_num=models.SmallIntegerField()
    update_date=models.DateField()

    class Meta:
        unique_together=('store_goods_type','order_num')
        ordering=('order_num',)


class StoreGoodsType(models.Model):
    store=models.ForeignKey(to="Stores",on_delete=models.CASCADE)











