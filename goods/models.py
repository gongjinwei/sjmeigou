from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class FirstClass(models.Model):
    first_class_name=models.CharField(max_length=100,help_text='一级类目名称')
    cover_path=models.ImageField(upload_to='sjmeigou/goods/firstclass/%Y%m%d')
    sort_order = models.SmallIntegerField(unique=True)
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.first_class_name

    class Meta:
        ordering = ['sort_order']


class SecondClass(models.Model):
    first_class=models.ForeignKey(to='FirstClass',on_delete=models.CASCADE,help_text='选择一级类目')
    second_class_name=models.CharField(max_length=100,help_text='填写二级类目名称')
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return "%s:%s" % (self.first_class.first_class_name,self.second_class_name)


class ThirdClass(models.Model):
    second_class=models.ForeignKey(to='SecondClass',on_delete=models.CASCADE,help_text='选择二级类目')
    third_class_name=models.CharField(max_length=100,help_text='填写三级类目名称')
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return "%s:%s:%s" % (self.second_class.first_class.first_class_name,self.second_class.second_class_name,self.third_class_name)


class FirstProperty(models.Model):
    first_property_name=models.CharField(max_length=100,help_text='填写类目属性')
    third_class=models.ForeignKey(to='ThirdClass',on_delete=models.CASCADE,blank=True,help_text='选择三级类目')
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return "%s:%s:%s:%s" % (self.third_class.second_class.first_class.first_class_name,self.third_class.second_class.second_class_name,self.third_class.third_class_name,self.first_property_name)


class SecondProperty(models.Model):
    second_property_name=models.CharField(max_length=100,help_text='填写二级属性名称')
    first_property=models.ForeignKey(to='FirstProperty',on_delete=models.CASCADE,help_text='选择一级属性')
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)
