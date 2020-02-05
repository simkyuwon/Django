from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import os, uuid
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.utils import timezone
# Create your models here.
def path_and_rename(instance, filename):
	upload_to = 'image'
	ext = filename.split('.')[-1]
	filename = '{}.{}'.format(uuid.uuid4(), ext)
	return os.path.join(upload_to, filename)

KINDS_OF_COMPANY = [
	('1CO','1CO'),
	('2CO','2CO'),
	('3CO','3CO'),
	('HQ','HQ'),
	('AD','admin'),
]

class UserManager(BaseUserManager):
	use_in_migrations = True

	def create_user(self, serviceNumber, name, company, password=None):
		if not serviceNumber :
			raise ValueError('must have user serviceNumber')
		user = self.model(
			serviceNumber = serviceNumber,
			name = name,
			company = company
		)
		user.is_active = False
		user.set_password(password)
		user.save(using=self._db)
		return user
	
	def create_superuser(self, serviceNumber, name, password):
		user = self.create_user(
			serviceNumber = serviceNumber,
			name = name,
			password = password,
		)
		user.is_active = True
		user.is_admin = True
		user.is_superuser = True
		user.is_staff = True
		user.save(using=self._db)
		return user

class User(AbstractBaseUser):
	serviceNumber = models.CharField(max_length=15, primary_key=True)
	name = models.CharField(max_length=5)
	company = models.CharField(max_length=3, choices=KINDS_OF_COMPANY)
	is_active = models.BooleanField(default=False)
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
	image = models.ImageField(upload_to=path_and_rename, blank=True)
	company = models.CharField(max_length=3, choices=KINDS_OF_COMPANY)

	def save(self):
		img = Image.open(self.image)
		output = BytesIO()
		width, height = img.size
		if width > height:
			if width > 480:
				height = int(height * 480 / width)
				width = 480
		else:
			if height > 480:
				width = int(width * 480 / height)
				height = 480
		resizeImg = img.resize((width, height))
		if img.format == 'PNG':
			resizeImg.save(output, 'PNG')
			output.seek(0)
			self.image = InMemoryUploadedFile(output, 'ImageField',"image/PNG", "%s"%self.image.name, sys.getsizeof(output), None)
		elif img.format == 'JPEG':
			resizeImg.save(output, 'JPEG')
			output.seek(0)
			self.image = InMemoryUploadedFile(output, 'ImageField',"image/JPEG", "%s"%self.image.name, sys.getsizeof(output), None)
		super(FireExtinguisherList, self).save()

	def update(self):
		super(FireExtinguisherList, self).save()

	def __str__(self):
		return self.place

@receiver(post_delete, sender=FireExtinguisherList)
def FireExtinguisherList_post_delete(sender, instance, **kwargs):
	if os.path.isfile(instance.image.path):
		os.remove(instance.image.path)

class InspectionDateList(models.Model):
	fireExtinguisher = models.ForeignKey(FireExtinguisherList , on_delete=models.SET_NULL, null=True)
	inspectionDate = models.DateTimeField(default = timezone.now)
	inspector = models.ForeignKey(User, on_delete = models.SET_NULL, null=True)
	result = models.TextField()
	action = models.TextField()

	def __str__(self):
		return self.fireExtinguisher.place
