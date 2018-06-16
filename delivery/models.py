from django.db import models

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