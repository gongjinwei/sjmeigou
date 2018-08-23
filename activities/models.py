from django.db import models

# Create your models here.


class ActivityImage(models.Model):
    image = models.ImageField(upload_to='sjmeigou/activity')
    image_type = models.SmallIntegerField(choices=((1,'白底图'),(2,'透明图')))
    create_time = models.DateTimeField(auto_now_add=True)


class BasicInfo(models.Model):
    title = models.CharField(max_length=14)
    white_bg_pic= models.OneToOneField(on_delete=models.CASCADE,to='ActivityImage',related_name='white_bg')
    transparent_pic = models.OneToOneField(on_delete=models.CASCADE,to='ActivityImage',related_name='trans_bg')
    profit = models.CharField(max_length=9)
    is_imported = models.BooleanField(default=False)
    purchase_limit=models.SmallIntegerField(default=0)