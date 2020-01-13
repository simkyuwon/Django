from django.db import models

# Create your models here.
class User(models.Model):
    serviceNumber = models.CharField(max_length=15, primary_key=True)
    name = models.CharField(max_length=20)

class FireExtinguisher(models.Model):
    name = models.CharField(max_length=20)
    inspectionDate = models.DateField()
    inspector = models.ForeignKey(User, on_delete = models.SET_NULL, null=True)
