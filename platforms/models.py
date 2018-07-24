import datetime,random

from decimal import Decimal
from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from index.models import Application


class CheckApplication(models.Model):
    application=models.ForeignKey(to=Application,on_delete=models.CASCADE)
    checker=models.ForeignKey(to=User,on_delete=models.DO_NOTHING,editable=False)
    apply_status=models.SmallIntegerField(choices=((2,'打款验证中'),(3,'审核通过'),(4,'审核不通过')))
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
    keep_account_no = models.CharField(max_length=30,primary_key=True)
    account_time = models.DateTimeField(auto_now_add=True)
    voucher = models.SmallIntegerField(choices=((1,'收'),(2,'付'),(3,'转'),(4,'记')))
    currency = models.CharField(max_length=20,default='CNY')
    money = models.PositiveIntegerField(help_text='发生金额（分）')
    remark = models.CharField(max_length=255)
    intercourse_business=models.ForeignKey(to='order.StoreOrder',null=True,on_delete=models.DO_NOTHING)
    settlement_method=models.CharField(max_length=30,default='微信支付')
    account = models.ForeignKey(to='Account',on_delete=models.DO_NOTHING)

    def save(self, *args,**kwargs):
        if self.keep_account_no:
            self.keep_account_no=datetime.datetime.strftime(datetime.datetime.now(),'%Y%m%d%H%M%S%f')+str(random.randint(10,100))
        super().save(*args,**kwargs)


class Account(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE,null=True)
    store = models.ForeignKey(to='store.Stores',on_delete=models.SET_NULL,null=True)
    account_type = models.IntegerField(choices=((1, '平台'), (2, '用户'), (3, '商户'), (4, '平台物流账号'),(5,'商户物流账号')))
    bank_balance = models.DecimalField(help_text='账户余额（元）',default=Decimal(0.00),max_digits=30,decimal_places=2,editable=False)
    receivable_balance = models.DecimalField(help_text='应收余额（元）',default=Decimal(0.00),max_digits=30,decimal_places=2,editable=False)
    payable_balance = models.DecimalField(help_text='应付余额（元）',default=Decimal(0.00),max_digits=30,decimal_places=2,editable=False)

    class Meta:
        unique_together=('user','store','account_type')


class AccountRecharge(models.Model):
    recharge_money = models.DecimalField(help_text='充值金额(元）',max_digits=30,decimal_places=2)
    recharge_type = models.SmallIntegerField(help_text='充值类型',choices=((1,'商家物流充值'),(2,'平台物流充值')))
    recharge_desc = models.CharField(help_text='充值描述',max_length=30)
    account = models.ForeignKey(to='Account',on_delete=models.DO_NOTHING,editable=False)
    recharge_time = models.DateTimeField(auto_now_add=True)
    recharge_result = models.BooleanField(default=False,editable=False)


class CodeWarehouse(models.Model):
    application=models.OneToOneField(to=Application,on_delete=models.DO_NOTHING)
    code=models.CharField(max_length=16,editable=False,unique=True)
    use_state=models.SmallIntegerField(choices=((0,'未使用'),(1,'已使用')),editable=False)
    active_user=models.ForeignKey(to=User,editable=False,null=True,blank=True,on_delete=models.SET_NULL)
    active_time=models.DateTimeField(auto_now=True)
    create_time=models.DateTimeField(auto_now_add=True)