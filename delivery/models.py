from django.db import models
import random,datetime

from django.contrib.auth.models import User

# Create your models here.


class OrderCallback(models.Model):
    order_original_id=models.CharField(max_length=50)
    order_status=models.IntegerField()
    cancel_reason=models.CharField(max_length=255,blank=True,null=True)
    abnormal_reason=models.CharField(max_length=255,blank=True,null=True)
    finish_reason=models.CharField(max_length=255,blank=True,null=True)
    rider_code=models.CharField(max_length=30,blank=True,null=True)
    rider_name=models.CharField(max_length=50,blank=True,null=True)
    rider_mobile=models.CharField(max_length=15,blank=True,null=True)
    time_status_update=models.BigIntegerField()
    sig=models.CharField(max_length=50)


class InitDwdOrder(models.Model):
    good_refund = models.ForeignKey(to='InitGoodRefund',on_delete=models.SET_NULL,null=True,related_name='dwd_init_order')
    dwd_store_order = models.ForeignKey(to='order.DwdOrder',on_delete=models.SET_NULL,null=True,related_name='dwd_init_order')
    has_paid = models.BooleanField(default=False)
    order_original_id = models.CharField(max_length=40,primary_key=True,editable=False)
    order_create_time = models.BigIntegerField()
    order_remark = models.CharField(max_length=128,blank=True,default='')
    order_price = models.PositiveIntegerField()
    cargo_weight= models.IntegerField(default=0)
    cargo_num=models.IntegerField(default=1)
    city_code=models.CharField(max_length=7)
    seller_id = models.CharField(max_length=40)
    seller_name=models.CharField(max_length=128)
    seller_mobile =models.CharField(max_length=12)
    seller_address = models.CharField(max_length=255)
    seller_lat=models.FloatField()
    seller_lng=models.FloatField()
    consignee_name=models.CharField(max_length=128)
    consignee_mobile=models.CharField(max_length=12)
    consignee_address = models.CharField(max_length=255)
    consignee_lat=models.FloatField(),
    consignee_lng=models.FloatField()
    money_rider_needpaid = models.PositiveIntegerField(default=0)
    money_rider_prepaid=models.PositiveIntegerField(default=0)
    money_rider_charge = models.PositiveIntegerField(default=0)
    time_waiting_at_seller = models.IntegerField(default=300)
    delivery_fee_from_seller=models.IntegerField(default=0)

    @property
    def trade_number(self):
        now = datetime.datetime.now()
        return datetime.datetime.strftime(now, 'DWD%Y%m%d%H%M%S%f') + str(random.randint(1000, 9999))


class InitGoodRefund(models.Model):
    store_order = models.ForeignKey(to='order.StoreOrder', on_delete=models.CASCADE,editable=False)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, editable=False)
    price = models.DecimalField(max_digits=30,decimal_places=2,help_text='元')
    distance = models.FloatField(null=True,editable=False)
    paid_money = models.DecimalField(max_digits=30,decimal_places=2,editable=False,null=True)
    paid_time = models.DateTimeField(editable=False,null=True)
    state = models.SmallIntegerField(editable=False,choices=((1,'未支付'),(2,'支付成功')),default=1)
    settlement = models.SmallIntegerField(choices=((1,'微信支付'),),default=1)
    create_time = models.DateTimeField(auto_now_add=True)
    remark = models.CharField(null=True,max_length=100)
    dwd_status = models.SmallIntegerField(choices=(
        (0, '系统派单中'), (3, '骑手已转单'), (5, '骑手已接单'), (10, '骑手已到店，等待商家发货'), (15, '骑手已离店，配送途中'), (98, '订单出现异常，骑手无法完成'),
        (99, '订单已取消'), (100, '骑手已妥投')), null=True)
    accept_time = models.DateTimeField(null=True, editable=False)
    user_arrive_time = models.DateTimeField(null=True, editable=False)
    arrive_time = models.DateTimeField(null=True, editable=False)
    rider_name = models.CharField(max_length=50, null=True,editable=False)
    rider_code = models.CharField(max_length=20, null=True,editable=False)
    rider_mobile = models.CharField(max_length=12, null=True,editable=False)
    cancel_reason = models.CharField(max_length=100, null=True,editable=False)
    dwd_order_id = models.CharField(max_length=50, null=True,editable=False)
    dwd_order_distance = models.IntegerField(null=True,editable=False)