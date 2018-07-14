from django.db import models
from django.contrib.auth.models import User

from decimal import Decimal


# Create your models here.


class ShoppingCarItem(models.Model):
    shopping_car = models.ForeignKey(to='ShoppingCar', on_delete=models.CASCADE, related_name='items', editable=False)
    price_of_added = models.DecimalField(decimal_places=2, max_digits=30, editable=False)
    num = models.IntegerField()
    sku = models.ForeignKey(to='goods.SKU', on_delete=models.CASCADE)
    total_money = models.DecimalField(max_digits=30, decimal_places=2, default=Decimal(0.00), editable=False)
    state = models.SmallIntegerField(choices=((0, '正常'), (1, '失效')), default=0, editable=False)
    create_time = models.DateTimeField(auto_now_add=True)

    def save(self, *args,**kwargs):
        self.total_money=self.num*self.sku.price
        super().save(*args,**kwargs)


class ShoppingCar(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='shopping_items', editable=False)
    store = models.ForeignKey(to='store.Stores', on_delete=models.CASCADE)


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
        ordering = ('-create_date',)

    def algorithm(self, money):
        discount=0
        if money>=self.threshold_count:
            discount=self.discount
        return ('%s:满%s减%s' % (self.name,self.threshold_count,self.discount),discount)


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
    store_activity_type = models.ForeignKey(to='StoreActivityType', on_delete=models.CASCADE)
    activity_name = models.CharField(max_length=20)
    datetime_from = models.DateTimeField()
    datetime_to = models.DateTimeField()
    select_all = models.BooleanField(default=True)
    threshold_num = models.IntegerField(default=0)
    threshold_money = models.DecimalField(default=Decimal(0.00), max_digits=30, decimal_places=2)
    bargain_price = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    limitation_per_user = models.IntegerField(default=0)
    discount = models.DecimalField(max_digits=2, decimal_places=1, null=True)
    discount_money = models.IntegerField(default=0)
    state = models.SmallIntegerField(choices=((0, '正常'), (1, '用户终止'), (2, '时间到期')), default=0, editable=False)
    create_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.activity_name

    class Meta:
        ordering = ('-create_time',)

    def algorithm(self, num, money):
        strategy = self.store_activity_type.type_strategy
        discount = 0
        if strategy == 1:
            if self.threshold_num == 0 or num >= self.threshold_num:
                discount = money * (1 - self.discount / 10)
            return ('%s:满%s件打%s折' % (self.activity_name, self.threshold_num, self.discount), discount)

        elif strategy == 2:
            if self.threshold_money == Decimal(0.00) or money >= self.threshold_money:
                discount = money * (1 - self.discount / 10)
            return ('%s:满%s打%s折' % (self.activity_name, self.threshold_money, self.discount), discount)

        elif strategy == 3:
            if self.threshold_num == 0 or num >= self.threshold_num:
                discount = self.discount_money
            return ('%s:满%s件减%s' % (self.activity_name, self.threshold_num, self.discount_money), discount)

        elif strategy == 4:
            if self.threshold_money == Decimal(0.00) or money >= self.threshold_money:
                discount = self.discount_money
            return ('%s:满%s减%s' % (self.activity_name, self.threshold_money, self.discount_money), discount)

        return ("不使用优惠", 0)


class JoinActivity(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, editable=False)
    activity = models.ForeignKey(to='StoreActivity', on_delete=models.CASCADE)
    nums_join = models.PositiveIntegerField(default=0, editable=False)
    update_time = models.DateTimeField(auto_now=True)


class StoreActivityType(models.Model):
    type_name = models.CharField(max_length=10)
    type_pic = models.ImageField(upload_to='sjmeigou/activity')
    type_strategy = models.SmallIntegerField(
        choices=((1, '满数量打折扣'), (2, '满金额打折扣'), (3, '满数量减金额'), (4, '满金额减金额'), (5, '取特价')), default=1)


class StoreActivitySelected(models.Model):
    activity = models.ForeignKey(to='StoreActivity', on_delete=models.CASCADE, related_name='selected_goods', null=True,
                                 editable=False)
    good = models.ForeignKey(to='goods.GoodDetail', on_delete=models.CASCADE)
    select_type = models.SmallIntegerField(choices=((0, '参与活动的商品'), (1, '赠品')), default=0, editable=False)


class UnifyOrder(models.Model):
    order_no = models.CharField(primary_key=True,editable=False,max_length=18)
    order_desc = models.CharField(max_length=100,editable=False)
    order_num = models.PositiveIntegerField(editable=False)
    account = models.DecimalField(editable=False,decimal_places=2,max_digits=30)
    account_paid = models.DecimalField(editable=False,decimal_places=2,max_digits=30)
    coupon = models.ForeignKey(to='Coupon',on_delete=models.DO_NOTHING,null=True)
    activity = models.ForeignKey(to='StoreActivity',on_delete=models.DO_NOTHING,null=True)
    deliver_server=models.ForeignKey(to='goods.DeliverServices',on_delete=models.DO_NOTHING)
    store = models.ForeignKey(to='store.Stores',on_delete=models.DO_NOTHING)
    user_message=models.CharField(max_length=255,default='',blank=True)
    user = models.ForeignKey(to=User,on_delete=models.DO_NOTHING,editable=False)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    state=models.SmallIntegerField(choices=((1,'待付款'),(2,'待发货'),(3,'待收货'),(4,'待评价'),(5,'已完成')),editable=False)


class OrderSku(models.Model):
    order = models.ForeignKey(to='UnifyOrder',on_delete=models.CASCADE,related_name='relate_sku')
    sku=models.ForeignKey(to='goods.SKU',on_delete=models.DO_NOTHING)
    num=models.IntegerField()


