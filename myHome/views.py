from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import User, FireExtinguisherList, InspectionDateList
from django.contrib import auth
from datetime import datetime
from django.urls import reverse
import requests
import json
# Create your views here.

def index(request):
	return render(request, "index.html")

def list(request, *args, **kwargs):
	if request.user.is_authenticated :
		user = request.user
		userList = User.objects.all()
		if request.GET.get('serviceNumber','') == 'all' :
			fireExtinguisherList = FireExtinguisherList.objects.all().order_by("place")
		elif request.GET.get('serviceNumber','') == '' :
			fireExtinguisherList = FireExtinguisherList.objects.filter(mainInspector = user.serviceNumber).order_by("place")
		else :
			fireExtinguisherList = FireExtinguisherList.objects.filter(mainInspector = request.GET.get('serviceNumber','')).order_by("place")
		if request.GET.get('serviceNumber','') == '' :
			context = {"fireExtinguisherList" : fireExtinguisherList, "userList" : userList, "serviceNumber" : user.serviceNumber}
		else :
			context = {"fireExtinguisherList" : fireExtinguisherList, "userList" : userList, "serviceNumber" : request.GET.get('serviceNumber','')}
		return render(request, "list.html", context)
	else :
		return index(request)

def addfireextinguisher(request, *args, **kwargs):
	if request.user.is_authenticated:
		if request.user.is_admin:
			userList = User.objects.all()
			context = {"user" : request.user, "userList" : userList}
			return render(request, "addfireextinguisher.html", context)
	return render(request, "index.html", {"error":"관리자 전용 기능입니다."})

def updatefireextinguisher(request, *args, **kwargs):
	if request.user.is_admin:
		if FireExtinguisherList.objects.filter(place = request.POST['place']).count() != 0:
			userList = User.objects.all()
			context = {"user" : request.user, "userList" : userList, "error" : "등록된 장소입니다."}
			return render(request, "addfireextinguisher.html", context)
		else:
			newData = FireExtinguisherList(place = request.POST['place'], lastInspectionDate = request.POST['lastinspectiondate'], mainInspector = User.objects.get(serviceNumber = request.POST['maininspector']))
			newData.save()	
	return index(request)	

def inspection(request, *args, **kwargs):
	fireExtinguisher = FireExtinguisherList.objects.filter(place = request.GET.get('place',''))
	context = {"fireExtinguisher" : fireExtinguisher}	
	return render(request, "inspection.html", context)

def inspectionupdate(request, *args, **kwargs):
	if request.user.is_authenticated:
		fireExtinguisher = FireExtinguisherList.objects.filter(place = request.GET.get('place',''))
		fireExtinguisher.update(lastInspectionDate = datetime.today())
		newData = InspectionDateList(fireExtinguisher = fireExtinguisher[0], inspector = request.user)
		newData.save()
		return index(request)
	else :
		return redirect('../login?next='+request.get_full_path())

def inspectionlist(request, *args, **kwargs):
	if request.user.is_authenticated :
		user = request.user
		userList = User.objects.all()
		if request.GET.get('serviceNumber','') == 'all' :
			inspectionDateList = InspectionDateList.objects.all().order_by("-inspectionDate")
		elif request.GET.get('serviceNumber','') == '' :
			inspectionDateList = InspectionDateList.objects.filter(inspector = user).order_by("-inspectionDate")
		else :
			inspectionDateList = InspectionDateList.objects.filter(inspector = request.GET.get('serviceNumber','')).order_by("-inspectionDate")
		if request.GET.get('serviceNumber','') == '' :
			context = {"inspectionDateList" : inspectionDateList, "userList" : userList, "serviceNumber" : user.serviceNumber}
		else :
			context = {"inspectionDateList" : inspectionDateList, "userList" : userList, "serviceNumber" : request.GET.get('serviceNumber','')}
		return render(request, "inspectionlist.html", context)
	else :
		return index(request)

def login(request, *args, **kwargs):
	if request.method == "POST":
		serviceNumber = request.POST['serviceNumber']
		password = request.POST['password']
		user = auth.authenticate(request, serviceNumber=serviceNumber, password=password)
		if user is not None:
			auth.login(request, user)
			if request.GET.get('next','') == '':
				return render(request, 'index.html')
			else:
				return redirect(request.GET.get('next',''))
		else:
			return render(request, 'login.html', {'serviceNumber':serviceNumber,'password':password,'error':'serviceNumber or password is incorrect'})
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

def qrreader(request):
	return render(request, 'qrreader.html')

def qrapi(request):
	files = {'file':request.FILES['qrimg']}
	response = requests.post("http://api.qrserver.com/v1/read-qr-code/", data = {"MAX_FILE_SIZE" : "1048576"},  files = files)
	responseJson = response.json()
	fireExtinguisher = FireExtinguisherList.objects.filter(id = responseJson[0]['symbol'][0]['data'])
	fireExtinguisher.update(lastInspectionDate = datetime.today())
	newData = InspectionDateList(fireExtinguisher = fireExtinguisher[0], inspector = request.user)
	newData.save()
	return index(request)
