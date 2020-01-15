from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import User, FireExtinguisherList, InspectionDateList
from django.contrib import auth
#from django.contrib.auth import authenticate, login as auth_login

# Create your views here.
def index(request):
	if request.user.is_authenticated : 
		user = request.user
		fireExtinguisherList = FireExtinguisherList.objects.filter(mainInspector = user.serviceNumber).order_by("place")
	else :
		fireExtinguisherList = FireExtinguisherList.objects.all().order_by("place")
	context = {"fireExtinguisherList" : fireExtinguisherList}
	return render(request, "index.html", context)

def login(request):
	if request.method == "POST":
		serviceNumber = request.POST['serviceNumber']
		password = request.POST['password']	
		user = auth.authenticate(request, serviceNumber=serviceNumber, password=password)
		if user is not None:
			auth.login(request, user)
			return index(request)
		else:
			return render(request, 'login.html', {'serviceNumber':serviceNumber,'password':password,'error':'iserviceNumber or password is incorrect'})
	else:
		return render(request, 'login.html')

def logout(request):
	auth.logout(request)
	return index(request)		

def signup(request):
	if request.method == "POST":
		if request.POST["password1"] == request.POST["password2"]:
			user = User.objects.create_user(
				serviceNumber = request.POST["serviceNumber"],
				password = request.POST["password1"],
				name = request.POST["name"],
			)
			auth.login(request, user)
			return index(request)
		return render(request, 'signup.html') 	
	else:
		return render(request, 'signup.html')
