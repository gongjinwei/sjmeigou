from django.db import models
from django.contrib.auth.models import User

# Create your models here.


# class ActivityImage(models.Model):
#     image = models.ImageField(upload_to='sjmeigou/activity/images')
#     image_type = models.SmallIntegerField(choices=((1,'白底图'),(2,'透明图')))
#     create_time = models.DateTimeField(auto_now_add=True)
#
#
# class BasicInfo(models.Model):
#     title = models.CharField(max_length=14)
#     white_bg_pic= models.OneToOneField(on_delete=models.CASCADE,to='ActivityImage',related_name='white_bg')
#     transparent_pic = models.OneToOneField(on_delete=models.CASCADE,to='ActivityImage',related_name='trans_bg')
#     profit = models.CharField(max_length=9)
#     is_imported = models.BooleanField(default=False)
#     purchase_limit=models.SmallIntegerField(default=0)
#
#
# class PriceStock(models.Model):
#     origin_price = models.DecimalField(editable=False,max_digits=30,decimal_places=2)
#     activity_price = models.DecimalField(max_digits=30,decimal_places=2)
#     stock_type= models.SmallIntegerField(choices=((1,'全部库存'),(2,'部分库存')))
#     activity_stock = models.IntegerField()
#
#
# class Activity(models.Model):
#     theme = models.CharField(max_length=50)
#     poster = models.ImageField(upload_to='sjmeigou/activity/poster')
#     description = models.TextField()
#     register_closing_time = models.DateTimeField(help_text='报名截止时间')
#     from_time = models.DateTimeField(help_text='起始时间')
#     to_time = models.DateTimeField(help_text='终止时间')
#     exhibition_position=models.IntegerField(help_text='展位数')
#     activity_type = models.SmallIntegerField(choices=((1,'砍价'),))
#
#
# class JoinActivity(models.Model):
#     user= models.ForeignKey(to=User,on_delete=models.CASCADE)
#     activity=models.ForeignKey(to='Activity',on_delete=models.CASCADE)
#     good = models.ForeignKey(to='goods.GoodDetail',on_delete=models.CASCADE)
#     state = models.SmallIntegerField(choices=((1,'待审核'),(2,'审核通过'),(3,'审核不通过')),default=1,editable=False)
#     opinion=models.CharField(max_length=256,null=True)
#     update_time = models.DateTimeField(auto_now=True)
#     create_time = models.DateTimeField(auto_now_add=True)