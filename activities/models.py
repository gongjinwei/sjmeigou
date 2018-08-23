from django.db import models

# Create your models here.


class ActivityImage(models.Model):
    image = models.ImageField(upload_to='sjmeigou/activity')
    image_type = models.SmallIntegerField(choices=((1,'白底图'),(2,'透明图')))
    create_time = models.DateTimeField(auto_now_add=True)


class BasicInfo(models.Model):
    title = models.CharField(max_length=14)
    white_bg_pic= models.OneToOneField(on_delete=models.CASCADE,to='ActivityImage')
    transparent_pic = models.OneToOneField(on_delete=models.CASCADE,to='ActivityImage')
    profit = models.CharField(max_length=9)
    is_imported = models.BooleanField(default=False)