from django.db import models

# Create your models here.


class BasicInfo(models.Model):
    title = models.CharField(max_length=14)
