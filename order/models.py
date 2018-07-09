from django.db import models
from django.contrib.auth.models import User

from decimal import Decimal


# Create your models here.


class ShoppingCarItem(models.Model):
    shopping_car = models.ForeignKey(to='ShoppingCar',on_delete=models.CASCADE,related_name='items',editable=False)
    price_of_added = models.DecimalField(decimal_places=2, max_digits=30, editable=False)
    num = models.IntegerField()
    sku = models.ForeignKey(to='goods.SKU', on_delete=models.CASCADE)
    state = models.SmallIntegerField(choices=((0, '正常'), (1, '失效')), default=0, editable=False)
    create_time = models.DateTimeField(auto_now_add=True)


class ShoppingCar(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='shopping_items', editable=False)
    store= models.ForeignKey(to='store.Stores',on_delete=models.CASCADE)


class Coupon(models.Model):
    store = models.ForeignKey(to='store.Stores', on_delete=models.CASCADE, related_name='coupons', editable=False)
    name = models.CharField(max_length=10)
    date_from = models.DateField()
    date_to = models.DateField()
    discount = models.IntegerField()
    threshold_count = models.IntegerField()
    available_num = models.IntegerField()
    limit_per_user = models.SmallIntegerField()
    create_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering=('-create_date',)


class GetCoupon(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, editable=False)
    coupon = models.ForeignKey(to=Coupon, on_delete=models.SET_NULL, null=True)
    has_num = models.SmallIntegerField(default=0, editable=False)


class CouponRecords(models.Model):
    get_coupon = models.ForeignKey(to='GetCoupon', on_delete=models.DO_NOTHING)
    action = models.IntegerField(choices=((0, '领取'), (1, '使用')), default=0)
    action_time = models.DateTimeField(auto_now=True)


class StoreActivity(models.Model):
    store = models.ForeignKey(to='store.Stores', on_delete=models.CASCADE, editable=False)
    store_activity_type=models.ForeignKey(to='StoreActivityType',on_delete=models.CASCADE)
    activity_name=models.CharField(max_length=20)
    datetime_from=models.DateTimeField()
    datetime_to=models.DateTimeField()
    select_all=models.BooleanField(default=True)
    threshold_num=models.IntegerField(default=0)
    threshold_money=models.DecimalField(default=Decimal(0.00),max_digits=30,decimal_places=2)
    bargain_price=models.DecimalField(max_digits=20,decimal_places=2,null=True)
    limitation_per_user=models.IntegerField(default=0)
    discount=models.DecimalField(max_digits=2,decimal_places=1,null=True)
    state=models.SmallIntegerField(choices=((0,'正常'),(1,'用户终止'),(2,'时间到期')),default=0)
    create_time=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.activity_name

    class Meta:
        ordering=('-create_time',)


class StoreActivityType(models.Model):
    type_name=models.CharField(max_length=10)
    type_pic=models.URLField(null=True)


class StoreActivitySelected(models.Model):
    activity=models.ForeignKey(to='StoreActivity',on_delete=models.CASCADE,related_name='selected_goods',null=True,editable=False)
    good=models.ForeignKey(to='goods.GoodDetail',on_delete=models.CASCADE)
    select_type=models.SmallIntegerField(choices=((0,'参与活动的商品'),(1,'赠品')),default=0,editable=False)



