from django.db import models
from django.contrib.auth.models import User

from decimal import Decimal
from datetime import datetime
import random

from platforms.models import AccountRecharge
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

    @property
    def act_name(self):
        return '满%s减%s' % (self.threshold_count,self.discount)


class GetCoupon(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, editable=False)
    coupon = models.ForeignKey(to=Coupon, on_delete=models.SET_NULL, null=True)
    has_num = models.SmallIntegerField(default=0, editable=False)


class CouponRecords(models.Model):
    user = models.ForeignKey(to=User,on_delete=models.DO_NOTHING)
    coupon = models.ForeignKey(to='Coupon', on_delete=models.DO_NOTHING)
    action = models.IntegerField(choices=((0, '领取'), (1, '使用')), default=0)
    action_num = models.IntegerField()
    action_time = models.DateTimeField(auto_now=True)


class StoreActivity(models.Model):
    store = models.ForeignKey(to='store.Stores', on_delete=models.CASCADE, editable=False)
    store_activity_type = models.ForeignKey(to='platforms.StoreActivityType', on_delete=models.CASCADE)
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

    @property
    def act_name(self):
        strategy = self.store_activity_type.type_strategy
        choice={
            1:'满%s件打%s折' % ( self.threshold_num, self.discount),
            2:'满%s打%s折' % ( self.threshold_money, self.discount),
            3:'满%s件减%s' % ( self.threshold_num, self.discount_money),
            4:'满%s减%s' % (self.threshold_money, self.discount_money)
        }
        return choice.get(strategy,'')


class JoinActivity(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, editable=False)
    activity = models.ForeignKey(to='StoreActivity', on_delete=models.CASCADE)
    nums_join = models.PositiveIntegerField(default=0, editable=False)
    update_time = models.DateTimeField(auto_now=True)


class StoreActivitySelected(models.Model):
    activity = models.ForeignKey(to='StoreActivity', on_delete=models.CASCADE, related_name='selected_goods', null=True,
                                 editable=False)
    good = models.ForeignKey(to='goods.GoodDetail', on_delete=models.CASCADE)
    select_type = models.SmallIntegerField(choices=((0, '参与活动的商品'), (1, '赠品')), default=0, editable=False)


class UnifyOrder(models.Model):
    order_no = models.CharField(primary_key=True,editable=False,max_length=18)
    order_desc = models.CharField(max_length=100,help_text='订单描述')
    price = models.DecimalField(max_digits=30,decimal_places=2,help_text='下单价格:元')
    account = models.DecimalField(editable=False,decimal_places=2,max_digits=30)
    account_paid = models.DecimalField(editable=False,decimal_places=2,max_digits=30,default=Decimal(0.00))
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True)
    paid_time = models.DateTimeField(editable=False, null=True)
    address = models.ForeignKey(to='ReceiveAddress',on_delete=models.SET_NULL,null=True)
    update_time = models.DateTimeField(auto_now=True)
    state=models.SmallIntegerField(choices=((1,'待付款'),(2,'待发货'),(3,'配送中'),(4, '配送完成待评价'), (5, '交易完成'),(6,'退款成功'),(7,'待退款'),(8,'订单已取消'),(9,'已完成用户删除'),(10,'部分支付')),editable=False,default=1)


class StoreOrder(models.Model):
    unify_order = models.ForeignKey(to='UnifyOrder',on_delete=models.CASCADE,related_name='store_orders',editable=False)
    store_order_no = models.CharField(primary_key=True,editable=False,max_length=18)
    coupon = models.ForeignKey(to='GetCoupon', on_delete=models.DO_NOTHING, null=True)
    activity = models.ForeignKey(to='StoreActivity', on_delete=models.DO_NOTHING, null=True)
    store = models.ForeignKey(to='store.Stores', on_delete=models.DO_NOTHING)
    account = models.DecimalField(editable=False, decimal_places=2, max_digits=30)
    account_paid = models.DecimalField(editable=False, decimal_places=2, max_digits=30, default=Decimal(0.00))
    paid_time = models.DateTimeField(editable=False,null=True)
    state = models.SmallIntegerField(choices=((1, '待付款'), (2, '待发货'), (3, '待收货'), (4, '已完成待评价'), (5, '交易完成'),(6,'退款成功'),(7,'待退款'),(8,'订单已取消'),(9,'已完成用户删除')),
                                     editable=False, default=1)
    deliver_server = models.ForeignKey(to='goods.GoodDeliver', on_delete=models.DO_NOTHING, null=True)
    deliver_payment = models.DecimalField(max_digits=30, decimal_places=2, default=Decimal(0.00),editable=False)
    deliver_distance = models.FloatField(help_text='配送距离',null=True,editable=False)
    store_to_pay = models.DecimalField(max_digits=30,decimal_places=2,default=Decimal(0.00),editable=False)
    user_message = models.CharField(max_length=255, default='', blank=True)
    update_time = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)

    class Meta:
        ordering=('update_time',)


class SkuOrder(models.Model):
    store_order = models.ForeignKey(to='StoreOrder',on_delete=models.CASCADE,related_name='sku_orders',editable=False)
    sku=models.ForeignKey(to='goods.SKU',on_delete=models.CASCADE)
    num=models.IntegerField()


class ReceiveAddress(models.Model):
    user = models.ForeignKey(to=User,on_delete=models.CASCADE,editable=False)
    contact=models.CharField(max_length=100)
    call = models.IntegerField(choices=((0,"先生"),(1,"女士")),null=True)
    phone = models.CharField(max_length=12)
    address = models.CharField(max_length=128)
    longitude = models.FloatField()
    latitude = models.FloatField()
    room_no = models.CharField(max_length=128)
    tag = models.CharField(choices=(("家","家"),("公司","公司"),("学校","学校")),null=True,max_length=10)
    postcode = models.CharField(max_length=7,null=True)
    is_default = models.BooleanField(default=False)


class InitiatePayment(models.Model):
    trade=models.OneToOneField(to='OrderTrade',on_delete=models.CASCADE)
    user = models.ForeignKey(to=User,on_delete=models.CASCADE)
    appId = models.CharField(max_length=100)
    timeStamp=models.CharField(max_length=30)
    nonceStr=models.CharField(max_length=40)
    package=models.CharField(max_length=128)
    signType=models.CharField(max_length=20,default='MD5')
    paySign=models.CharField(max_length=50)
    create_time=models.DateTimeField(auto_now_add=True)
    has_paid = models.BooleanField(default=False)


class OrderComment(models.Model):
    order = models.OneToOneField(to='StoreOrder',on_delete=models.CASCADE)
    state=models.SmallIntegerField(choices=((0,'买家已评价'),(1,'卖家已评价'),(2,'双方已评')),editable=False)
    buyer_comment=models.OneToOneField(to='CommentContent',on_delete=models.CASCADE)
    seller_comment = models.OneToOneField(to='CommentContent',on_delete=models.CASCADE)


class CommentContent(models.Model):
    comment = models.CharField(max_length=255)
    score = models.SmallIntegerField(choices=((1, '很差'), (2, '一般'), (3, '满意'), (4, '非常满意'), (5, '完美')))
    comment_time=models.DateTimeField()


class OrderTrade(models.Model):
    store_order = models.ForeignKey(to='StoreOrder',on_delete=models.CASCADE,null=True)
    unify_order = models.ForeignKey(to='UnifyOrder',on_delete=models.CASCADE,null=True)
    recharge = models.ForeignKey(to=AccountRecharge,on_delete=models.CASCADE,null=True)
    trade_no = models.CharField(primary_key=True,max_length=30)
    paid_time=models.DateTimeField(null=True,editable=False)
    paid_money = models.DecimalField(default=Decimal(0.00),max_digits=30,decimal_places=2,editable=False)
    create_time = models.DateTimeField(auto_now_add=True)

    @property
    def trade_number(self):
        now = datetime.now()
        return datetime.strftime(now,'%Y%m%d%H%M%S%f')+str(random.randint(1000,9999))

    def save(self, *args,**kwargs):
        if not self.trade_no:
            self.trade_no=self.trade_number
        super().save(*args,**kwargs)


class DwdOrder(models.Model):
    store_order=models.OneToOneField(to='StoreOrder',on_delete=models.DO_NOTHING,related_name='dwd_order_info')
    dwd_status=models.SmallIntegerField(choices=((0,'系统派单中'),(3,'骑手已转单'),(5,'骑手已接单'),(10,'骑手已到店，等待商家发货'),(15,'骑手已离店，配送途中'),(98,'订单出现异常，骑手无法完成'),(99,'订单已取消'),(100,'骑手已妥投')),null=True)
    rider_name=models.CharField(max_length=50,null=True)
    rider_code=models.CharField(max_length=20,null=True)
    rider_mobile = models.CharField(max_length=12,null=True)
    cancel_reason = models.CharField(max_length=100,null=True)
    dwd_order_id=models.CharField(max_length=50,null=True)
    dwd_order_distance=models.IntegerField(null=True)





