from django.db import models
from django.contrib.auth.models import User
from jsonfield import JSONField


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
    contract_name = models.CharField(max_length=100)
    contract_mobile = models.CharField(max_length=12)
    reference_code = models.CharField(max_length=50, default='', null=True, blank=True)
    social_credit_code = models.CharField(max_length=18)
    store_name = models.CharField(max_length=100)
    store_phone = models.CharField(max_length=13,null=True,blank=True)
    store_licence_pic = models.URLField()
    store_business_scope = models.TextField()
    store_address = models.CharField(max_length=255)
    longitude = models.FloatField()
    latitude = models.FloatField()
    receiver_account_num = models.CharField(max_length=30)
    receiver_bank_name = models.CharField(max_length=128)
    receiver_name = models.CharField(max_length=50)
    receiver_bank_no = models.IntegerField()
    form_id = models.CharField(max_length=30, blank=True, null=True)
    application_status = models.SmallIntegerField(choices=((1, '审核中'), (2, '打款验证中'), (3, '审核通过')), editable=False,
                                                  default=1)
    application_user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    application_time = models.DateTimeField(auto_now_add=True, editable=False)


class StoreImage(models.Model):
    application = models.ForeignKey(to='Application', on_delete=models.CASCADE, related_name='store_images',
                                    editable=False,null=True,blank=True)
    store_image = models.URLField(blank=True, null=True)
