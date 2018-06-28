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