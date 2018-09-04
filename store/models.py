import string

from django.db import models
from django.contrib.auth.models import User
from index.models import Application
from decimal import Decimal

# Create your models here.

store_deposit=1000


class Stores(models.Model):
    info=models.OneToOneField(to=Application,on_delete=models.CASCADE)
    active_code=models.CharField(max_length=20,default='')
    name=models.CharField(max_length=50,default='',editable=False)
    business_hour_from=models.TimeField()
    business_hour_to=models.TimeField()
    logo=models.URLField(default='https://image.sjmeigou.com/sjmeigou/20180707/0f8c068938abc703a1604a1aa4.jpg')
    receive_address=models.CharField(null=True,max_length=128)
    longitude = models.FloatField(null=True)
    latitude = models.FloatField(null=True)
    profile = models.CharField(max_length=1024,null=True)
    adcode = models.CharField(max_length=6,default='330700')
    take_off = models.DecimalField(max_digits=10,decimal_places=1,default=Decimal(50.0),help_text='起送价')
    store_phone=models.CharField(max_length=12,null=True)
    active_state=models.SmallIntegerField(default=0,editable=False)
    user=models.OneToOneField(to=User,editable=False,on_delete=models.CASCADE)
    create_time=models.DateTimeField(auto_now_add=True,editable=False)
    update_time=models.DateTimeField(auto_now=True,editable=False)

    def __str__(self):
        return self.name


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


class StoreFavorites(models.Model):
    store = models.ForeignKey(to="Stores", on_delete=models.CASCADE,related_name='favorites')
    user = models.ForeignKey(to=User,on_delete=models.CASCADE,editable=False,related_name='store_favorites')
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        ordering=('-update_time',)


class GoodFavorites(models.Model):
    good = models.ForeignKey(to="goods.GoodDetail", on_delete=models.CASCADE,related_name='favorites')
    user = models.ForeignKey(to=User,on_delete=models.CASCADE,editable=False,related_name='good_favorites')
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        ordering=('-update_time',)


class BargainActivity(models.Model):
    sku = models.ForeignKey(to='goods.SKU',on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    poster = models.ForeignKey(to='platforms.BargainPoster',on_delete=models.CASCADE)
    from_time = models.DateTimeField(help_text='起始时间')
    to_time = models.DateTimeField(help_text='终止时间')
    store = models.ForeignKey(to='Stores',on_delete=models.CASCADE,editable=False,related_name='bargain_activities')
    state = models.SmallIntegerField(choices=((1,'正常'),(2,'终止')),editable=False,default=1)
    activity_stock = models.IntegerField()
    origin_price = models.FloatField(editable=False)
    min_price = models.FloatField()
    cut_price_from = models.FloatField()
    cut_price_to = models.FloatField()


class UserBargain(models.Model):
    user = models.ForeignKey(to=User,on_delete=models.CASCADE,editable=False)
    activity = models.ForeignKey(to='BargainActivity',on_delete=models.CASCADE,related_name='user_bargains')
    price_now = models.FloatField(editable=False)
    had_paid = models.BooleanField(default=False,editable=False)
    paid_money = models.DecimalField(null=True,editable=False,max_digits=30,decimal_places=2)
    create_time = models.DateTimeField(auto_now_add=True)


class HelpCutPrice(models.Model):
    userId = models.ForeignKey(to='register.UserInfo',on_delete=models.CASCADE)
    cut_price = models.FloatField(editable=False)
    instant_price = models.FloatField(editable=False,default=0)
    user_bargain = models.ForeignKey(to='UserBargain',on_delete=models.CASCADE,editable=False,related_name='help_cuts')
    join_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=('-join_time',)


class BargainOrder(models.Model):
    user_bargain = models.ForeignKey(to='UserBargain',on_delete=models.CASCADE,editable=False,related_name='bargain_orders')
    balance_time = models.DateTimeField()
    price = models.DecimalField(max_digits=30,decimal_places=2)
    store_order = models.ForeignKey(to='order.StoreOrder',on_delete=models.CASCADE,related_name='bargain_orders')


class SharingReduceActivity(models.Model):
    store =models.ForeignKey(to='Stores',on_delete=models.CASCADE,editable=False,related_name='sharing_activities')
    is_ended = models.BooleanField(default=False)
    reduce_money = models.DecimalField(max_digits=5,decimal_places=1)


class JoinSharingReduce(models.Model):
    user = models.ForeignKey(to=User,on_delete=models.CASCADE,editable=False)
    sharing_activity = models.ForeignKey(to='store.SharingReduceActivity',on_delete=models.CASCADE,editable=False)
    sharing_times = models.IntegerField(default=1,editable=False)
    has_paid = models.BooleanField(default=False,editable=False)

