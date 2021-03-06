from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache

from django_redis import get_redis_connection

client=get_redis_connection("default")


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


class RecruitMerchant(models.Model):
    name = models.CharField(max_length=50, default='propagate', editable=False)
    image = models.ImageField(upload_to='sjmeigou/index/recruit/%Y%m%d')
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)


class Application(models.Model):
    application_id=models.CharField(default='0',primary_key=True,editable=False,max_length=20)
    contract_name = models.CharField(max_length=100)
    contract_mobile = models.CharField(max_length=12)
    reference_code = models.CharField(max_length=50, default='', null=True, blank=True)
    social_credit_code = models.CharField(max_length=18)
    store_name = models.CharField(max_length=100)
    store_phone = models.CharField(max_length=13, null=True, blank=True)
    store_business_scope = models.TextField()
    store_address = models.CharField(max_length=255)
    store_licence_pic = models.URLField()
    license_unit_name = models.CharField(max_length=128)
    license_legal_representative = models.CharField(max_length=128)
    longitude = models.FloatField()
    latitude = models.FloatField()
    adcode = models.CharField(max_length=6,default='330700')
    form_id = models.CharField(max_length=50, blank=True, null=True)
    application_status = models.SmallIntegerField(choices=((1, '审核中'), (2, '打款验证中'), (3, '审核通过'),(4,'审核不通过'),(5,'待激活'),(6,'正常')), editable=False,
                                                  default=1)
    application_user = models.OneToOneField(to=User, on_delete=models.CASCADE, editable=False)
    protocol_agreement=models.BooleanField(default=True)
    application_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time=models.DateTimeField(auto_now=True,editable=False)

    def save(self, *args,**kwargs):
        application_num=client.incr('application_num',1)
        self.application_id='%s%06d' %("SQ3307822018",application_num)

        super().save(*args,**kwargs)

    def __str__(self):
        return self.application_id


class StoreImage(models.Model):
    application = models.ForeignKey(to='Application', on_delete=models.CASCADE, related_name='store_images',
                                    editable=False, null=True, blank=True)
    store_image = models.URLField(blank=True, null=True)


class GoodTrack(models.Model):
    user = models.ForeignKey(to=User,on_delete=models.CASCADE,related_name='good_tracks',editable=False)
    good = models.ForeignKey(to='goods.GoodDetail',on_delete=models.CASCADE,related_name='tracks')
    date = models.DateField(auto_now=True)
    latest_time = models.DateTimeField(auto_now=True)
    visible = models.BooleanField(default=True,editable=False)

    class Meta:
        ordering=('-latest_time',)

