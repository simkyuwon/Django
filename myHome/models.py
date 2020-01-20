from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
# Create your models here.
class UserManager(BaseUserManager):
	use_in_migrations = True

	def create_user(self, serviceNumber, name, password=None):
		if not serviceNumber :
			raise ValueError('must have user serviceNumber')
		user = self.model(
			serviceNumber = serviceNumber,
			name = name
		)
		user.set_password(password)
		user.save(using=self._db)
		return user
	
	def create_superuser(self, serviceNumber, name, password):
		user = self.create_user(
			serviceNumber = serviceNumber,
			name = name,
			password = password,
		)
		user.is_admin = True
		user.is_superuser = True
		user.is_staff = True
		user.save(using=self._db)
		return user

class User(AbstractBaseUser):
	serviceNumber = models.CharField(max_length=15, primary_key=True)
	name = models.CharField(max_length=20)
	is_active = models.BooleanField(default=True)
	is_admin = models.BooleanField(default=False)
	is_superuser = models.BooleanField(default=False)
	is_staff = models.BooleanField(default=False)

	objects = UserManager()

	USERNAME_FIELD = 'serviceNumber'
	REQUIRED_FIELDS = ['name']	
	
	def has_perm(self, perm, obj=None):
		return True

	def has_module_perms(self, app_labe):
		return True	
	
	def is_staff(self):
		return self.is_admin
	
	def __str__(self):
		return self.name

class FireExtinguisherList(models.Model):
	place = models.CharField(max_length=20)
	lastInspectionDate = models.DateField()
	mainInspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

	def __str__(self):
		return self.place

class InspectionDateList(models.Model):
	fireExtinguisher = models.ForeignKey(FireExtinguisherList , on_delete=models.SET_NULL, null=True)
	inspectionDate = models.DateTimeField(auto_now=True)
	inspector = models.ForeignKey(User, on_delete = models.SET_NULL, null=True)

	def __str__(self):
		return self.fireExtinguisher.place
