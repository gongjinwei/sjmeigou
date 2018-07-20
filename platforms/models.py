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