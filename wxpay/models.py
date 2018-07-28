from django.db import models

# Create your models here.


class NotifyOrderModel(models.Model):
    return_code=models.CharField(max_length=16)
    return_msg=models.CharField(max_length=128,null=True,blank=True)
    appid=models.CharField(max_length=32,null=True,blank=True)
    mch_id=models.CharField(max_length=32,null=True,blank=True)
    device_info=models.CharField(max_length=32,null=True,blank=True)
    nonce_str=models.CharField(max_length=32,null=True,blank=True)
    sign=models.CharField(max_length=32,null=True,blank=True)
    sign_type=models.CharField(max_length=32,null=True,blank=True)
    result_code=models.CharField(max_length=16,null=True,blank=True)
    err_code=models.CharField(max_length=32,null=True,blank=True)
    err_code_des=models.CharField(max_length=128,null=True,blank=True)
    openid=models.CharField(max_length=128,null=True,blank=True)
    is_subscribe=models.CharField(max_length=1,null=True,blank=True)
    trade_type=models.CharField(max_length=16,null=True,blank=True)
    bank_type=models.CharField(max_length=16,null=True,blank=True)
    total_fee=models.IntegerField(null=True,blank=True)
    settlement_total_fee =models.IntegerField(null=True,blank=True)
    fee_type=models.CharField(max_length=8,null=True,blank=True)
    cash_fee=models.IntegerField(null=True,blank=True)
    cash_fee_type=models.CharField(max_length=16,null=True,blank=True)
    coupon_fee=models.IntegerField(null=True,blank=True)
    coupon_count=models.IntegerField(null=True,blank=True)
    coupon_type_0=models.CharField(max_length=8,null=True,blank=True)
    coupon_id_0=models.CharField(max_length=20,null=True,blank=True)
    coupon_fee_0=models.IntegerField(null=True,blank=True)
    transaction_id=models.CharField(max_length=32,null=True,blank=True)
    out_trade_no=models.CharField(max_length=32,null=True,blank=True)
    attach=models.CharField(max_length=128,null=True,blank=True)
    time_end=models.CharField(max_length=14,null=True,blank=True)


