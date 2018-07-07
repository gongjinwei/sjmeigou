from django.db import models
from django.contrib.auth.models import User

from decimal import Decimal


# Create your models here.


class ShoppingCarItem(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='shopping_items', editable=False)
    price_of_added = models.DecimalField(decimal_places=2, max_digits=30, editable=False)
    num = models.IntegerField()
    sku = models.ForeignKey(to='goods.SKU', on_delete=models.SET_NULL, null=True)
    state = models.SmallIntegerField(choices=((0, '正常'), (1, '失效')), default=0, editable=False)
    create_time = models.DateTimeField(auto_now_add=True)


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


class ReductionActivity(models.Model):
    store=models.ForeignKey(to='store.Stores',on_delete=models.CASCADE,editable=False)
    activity_name=models.CharField(max_length=20)
    datetime_from=models.DateTimeField()
    datetime_to=models.DateTimeField()
    select_all=models.BooleanField(default=True)
    threshold_num=models.IntegerField()
    discount=models.DecimalField(max_digits=3,decimal_places=1,default=Decimal(10.0))
    create_time=models.DateTimeField(auto_now_add=True)


class ReductionSelected(models.Model):
    activity=models.ForeignKey(to='ReductionActivity',on_delete=models.CASCADE,related_name='selected_goods',null=True,editable=False)
    good=models.ForeignKey(to='goods.GoodDetail',on_delete=models.CASCADE)
    select_type=models.SmallIntegerField(choices=((0,'参与活动的商品'),(1,'赠品')),default=0,editable=False)



