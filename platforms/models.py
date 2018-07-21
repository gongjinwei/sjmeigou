from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from index.models import Application


class CheckApplication(models.Model):
    application=models.ForeignKey(to=Application,on_delete=models.CASCADE)
    checker=models.ForeignKey(to=User,on_delete=models.DO_NOTHING,editable=False)
    apply_status=models.SmallIntegerField(choices=((2,'打款验证中'),(4,'审核不通过')))
    opinion=models.CharField(max_length=255,help_text='审核意见')
    check_time=models.DateTimeField(auto_now=True,editable=False)


class DeliverServices(models.Model):
    server_name=models.CharField(max_length=20)

    def __str__(self):
        return self.server_name


# 具体配送者，如点我达等
class Delivers(models.Model):
    deliver_server=models.ForeignKey(to='DeliverServices',on_delete=models.CASCADE,related_name='delivers')
    name = models.CharField(max_length=20)


class StoreActivityType(models.Model):
    type_name = models.CharField(max_length=10)
    type_pic = models.ImageField(upload_to='sjmeigou/activity')
    type_strategy = models.SmallIntegerField(
        choices=((1, '满数量打折扣'), (2, '满金额打折扣'), (3, '满数量减金额'), (4, '满金额减金额'), (5, '取特价')), default=1)


class KeepAccounts(models.Model):
    account_no = models.CharField(max_length=30,primary_key=True)
    account_time=models.DateTimeField(auto_now_add=True)
    voucher = models.SmallIntegerField(choices=((1,'收'),(2,'付'),(3,'转'),(4,'记')))
    currency = models.CharField(max_length=20,default='CNY')
    money =models.PositiveIntegerField(help_text='发生金额（分）')
    remark = models.CharField(max_length=255)
    intercourse_business=models.ForeignKey(to='order.StoreOrder',null=True,on_delete=models.DO_NOTHING)
    settlement_method=models.CharField(max_length=30,default='微信支付')
    account = models.ForeignKey(to='Account',on_delete=models.DO_NOTHING)


class Account(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE,null=True)
    user_type = models.IntegerField(choices=((1, '平台'), (2, '用户'), (3, '商户'), (4, '平台物流账号'),(5,'商户物流账号')))
    bank_balance = models.IntegerField(help_text='账户余额（分）',default=0)