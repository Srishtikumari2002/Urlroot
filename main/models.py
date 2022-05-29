from django.db import models

# Create your models here.
class Urlroot(models.Model):
    link = models.CharField(max_length = 1000)
    short = models.CharField(max_length = 10, unique=True)
    creator = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=False)
    published = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=200, blank=True, null=False, default='')

    class Meta:
        db_table = 'urlroot'
        ordering = ['published']
