from django.db import models
from django.contrib.auth.models import User


# Create your models here.


class Banner(models.Model):
    banner_type = models.CharField(choices=(("platform", "platform"), ("store", "store"), ("good", "good")),
                                   max_length=10)
    link_to = models.CharField(max_length=50)
    banner_path = models.ImageField(upload_to='sjmeigou/index/banner/%Y%m%d')
    banner_order = models.SmallIntegerField(unique=True)
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ['banner_order']


class SortType(models.Model):
    sort_name = models.CharField(max_length=50)
    cover_path = models.ImageField(upload_to='sjmeigou/index/sort/%Y%m%d')
    sort_order = models.SmallIntegerField(unique=True)
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ['sort_order']


class RecruitMerchant(models.Model):
    name=models.CharField(max_length=50,default='propagate',editable=False)
    image=models.ImageField(upload_to='sjmeigou/index/recruit/%Y%m%d')
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)


