from django.contrib import admin
from django.contrib.auth.models import Group
from .models import User, FireExtinguisherList, InspectionDateList

# Register your models here.
class UserAdmi(admin.ModelAdmin):
	pass
admin.site.register(User)
admin.site.register(FireExtinguisherList)
admin.site.register(InspectionDateList)
