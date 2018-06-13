from django.db import models
from django.contrib.auth.models import User


# Create your models here.


class FirstClass(models.Model):
    first_class_name = models.CharField(max_length=100, help_text='一级类目名称', unique=True)
    cover_path = models.ImageField(upload_to='sjmeigou/goods/firstclass/%Y%m%d')
    sort_order = models.SmallIntegerField(unique=True)
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.first_class_name

    class Meta:
        ordering = ['sort_order']


class SecondClass(models.Model):
    first_class = models.ForeignKey(to='FirstClass', on_delete=models.CASCADE, help_text='选择一级类目',
                                    related_name='second_classes')
    second_class_name = models.CharField(max_length=100, help_text='填写二级类目名称')
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return "%s:%s" % (self.first_class.first_class_name, self.second_class_name)

    class Meta:
        unique_together = ['first_class', 'second_class_name']


class ThirdClass(models.Model):
    second_class = models.ForeignKey(to='SecondClass', on_delete=models.CASCADE, help_text='选择二级类目')
    third_class_name = models.CharField(max_length=100, help_text='填写三级类目名称')
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return "%s:%s:%s" % (
        self.second_class.first_class.first_class_name, self.second_class.second_class_name, self.third_class_name)

    class Meta:
        unique_together = ['second_class', 'third_class_name']


class FirstProperty(models.Model):
    first_property_name = models.CharField(max_length=100, help_text='填写类目属性')
    third_class = models.ForeignKey(to='ThirdClass', on_delete=models.CASCADE, blank=True, help_text='选择三级类目')
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return "%s:%s:%s:%s" % (
        self.third_class.second_class.first_class.first_class_name, self.third_class.second_class.second_class_name,
        self.third_class.third_class_name, self.first_property_name)

    class Meta:
        unique_together = ['third_class', 'first_property_name']


class SecondProperty(models.Model):
    second_property_name = models.CharField(max_length=100, help_text='填写二级属性名称')
    first_property = models.ForeignKey(to='FirstProperty', on_delete=models.CASCADE, help_text='选择一级属性',
                                       related_name='secondProperties')
    last_operator = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, editable=False)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        unique_together = ['first_property', 'second_property_name']


class ItemDesc(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.DO_NOTHING, related_name='itemDescriptions', editable=False)
    item_order = models.IntegerField()
    item_type = models.IntegerField()
    item_content = models.CharField(max_length=255)
    create_time = models.DateTimeField(auto_now_add=True, editable=False)
    update_time = models.DateTimeField(auto_now=True, editable=False)


class SizeGroup(models.Model):
    group_name = models.CharField(max_length=50)
    third_class = models.ForeignKey(to='ThirdClass', on_delete=models.CASCADE)


class SizeDesc(models.Model):
    size_group = models.ForeignKey(to='SizeGroup', on_delete=models.CASCADE,related_name='sizes')
    size_name = models.CharField(max_length=50)
