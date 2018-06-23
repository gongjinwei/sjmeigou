from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string

# Create your models here.


class CheckApplication(models.Model):
    checker=models.ForeignKey(to=User,on_delete=models.CASCADE,editable=False)
    apply_status=models.SmallIntegerField(choices=((2,'打款验证中'),(4,'审核不通过')))
    opinion=models.CharField(max_length=255,help_text='审核意见')
    check_time=models.DateTimeField(auto_now=True,editable=False)


# class Classification(models.Model):
#     shop = models.CharField()
