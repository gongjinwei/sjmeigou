from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string

# Create your models here.


class Store(models.Model):
    application=models.OneToOneField(to='index.models.Application',on_delete=models.CASCADE)
    business_hours_from=models.TimeField()
    business_hours_to=models.TimeField()
    create_time=models.DateTimeField(auto_now_add=True,editable=False)
    update_time=models.DateTimeField(auto_now=True,editable=False)


class Classification(models.Model):
    shop = models.CharField()
