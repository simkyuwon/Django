from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import User, FireExtinguisherList, InspectionDateList
from django.contrib import auth
from datetime import datetime
from django.urls import reverse
from django.db.models import Q
from django.contrib.auth.hashers import check_password
import requests
import json
from PIL import Image
from io import BytesIO
# Create your views here.

def index(request):
	return render(request, "index.html")

def list(request, *args, **kwargs):
	if request.user.is_authenticated :
		user = request.user
		userList = User.objects.all()
		getServiceNumber = request.GET.get('serviceNumber','')	
		getSearch = request.GET.get('search','')
		getMode = request.GET.get('mode','')
		getFireExtinguisher = request.GET.getlist('fireextinguisher','')
		if getMode == 'add':	
			return addfireextinguisher(request) 
		if getMode == 'delete' :
			fireExtinguisherList = FireExtinguisherList.objects.filter(id__in = getFireExtinguisher)
			fireExtinguisherList.delete()
		if getServiceNumber == 'all' :
			fireExtinguisherList = FireExtinguisherList.objects.all().order_by("place")
		elif getServiceNumber == '' :
			fireExtinguisherList = FireExtinguisherList.objects.filter(mainInspector = user.serviceNumber).order_by("place")
		else :
			fireExtinguisherList = FireExtinguisherList.objects.filter(mainInspector = getServiceNumber).order_by("place")
		if getSearch :
			fireExtinguisherList = fireExtinguisherList.filter(Q(place__icontains=getSearch)|Q(mainInspector__name__icontains=getSearch))
		if getServiceNumber == '' :
			context = {"fireExtinguisherList" : fireExtinguisherList, "userList" : userList, "serviceNumber" : user.serviceNumber, "search" : getSearch}
		else :
			context = {"fireExtinguisherList" : fireExtinguisherList, "userList" : userList, "serviceNumber" : getServiceNumber, "search" : getSearch}
		if getMode == 'qr':
			return render(request, "qrlist.html", context)
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
		getServiceNumber = request.GET.get('serviceNumber','')
		getSearch = request.GET.get('search','')
		getInspectionDate = request.GET.get('inspectiondate','')
		if request.GET.get('delete','') != '' and getInspectionDate is not None:
			inspectionDateList = InspectionDateList.objects.filter(id__in = getInspectionDate)
			inspectionDateList.delete()	
		if getServiceNumber == 'all' :
			inspectionDateList = InspectionDateList.objects.all().order_by("-inspectionDate")
		elif getServiceNumber == '' :
			inspectionDateList = InspectionDateList.objects.filter(inspector = user).order_by("-inspectionDate")
		else :
			inspectionDateList = InspectionDateList.objects.filter(inspector = getServiceNumber).order_by("-inspectionDate")
		if getSearch :
			inspectionDateList = inspectionDateList.filter(Q(fireExtinguisher__place__icontains = getSearch)|Q(inspector__name__icontains = getSearch))
		if getServiceNumber == '' :
			context = {"inspectionDateList" : inspectionDateList, "userList" : userList, "serviceNumber" : user.serviceNumber}
		else :
			context = {"inspectionDateList" : inspectionDateList, "userList" : userList, "serviceNumber" : getServiceNumber}
		return render(request, "inspectionlist.html", context)
	else :
		return index(request)

def userlist(request):
	if request.user.is_authenticated :
		if not request.user.is_admin :
			return render(request, "index.html", {"error" : "관리자 전용 기능입니다."})
		user = request.user
		userList = User.objects.all()
		context = {"userList" : userList}	
		return render(request, "userlist.html", context)
	else :
		return index(request)

def updateuser(request):
	if request.method == "POST":
		newPassword = request.POST["password1"]
		user = User.objects.get(serviceNumber = request.POST['serviceNumber'])
		originPassword = user.password
		if newPassword != '' :
			if request.user.is_admin :
				if newPassword == request.POST["password2"] :
					user.set_password(newPassword)
			else :	
				if not check_password(request.POST['originpassword'], originPassword):
					return render(request, 'updateuser.html', {"User" : user, "error" : "비밀번호가 틀렸습니다."})
				if len(newPassword) < 8 :
					return render(request, 'updateuser.html', {"User" : user, "error" : "비밀번호는 8자 이상이어야 합니다."})
				if newPassword == request.POST["password2"] :
					user.set_password(newPassword)
				else :
					return render(request, 'updateuser.html', {"User" : user, "error" : "비밀번호가 다릅니다."})
		if request.POST.get("adminAuth",""):
			user.is_admin = True
		else :
			user.is_admin = False
		user.name = request.POST["name"]
		user.save()
		if request.user.serviceNumber == request.POST["serviceNumber"] :
			auth.login(request, user)
		return render(request, 'index.html')	
	else :
		user = User.objects.get(serviceNumber = request.GET.get('serviceNumber',''))
		return render(request, 'updateuser.html', {"User" : user})	

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
		password = request.POST["password1"]
		if len(password) < 8:
			return render(request, 'signup.html', {"error" : "비밀번호는 8자 이상이어야 합니다."})
		if password == request.POST["password2"]:
			user = User.objects.create_user(
				serviceNumber = request.POST["serviceNumber"],
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
	if request.POST['qrdata'] != '' :
		fireExtinguisher = FireExtinguisherList.objects.get(id = request.POST['qrdata'])
	else :
		if 'qrimg' not in request.FILES:
			return render(request,'qrreader.html', {'error':'파일 없음'})
		files = {'file':request.FILES['qrimg']}
		img_file = BytesIO(files['file'].read())
		img = Image.open(img_file)
		resize_img = img.resize((int(img.size[0] * 0.5), int(img.size[1] * 0.5)))
		buf = BytesIO()
		resize_img.save(buf, format='PNG')
		files = {'file':buf.getvalue()}
		response = requests.post("http://api.qrserver.com/v1/read-qr-code/", data = {"MAX_FILE_SIZE" : "1048576"},  files = files)
		responseJson = response.json()
		if responseJson[0]['symbol'][0]['error'] == "could not find/read QR Code":
			return render(request, 'qrreader.html', {'error' : 'Qr code 인식 안됨'})
		fireExtinguisher = FireExtinguisherList.objects.get(id = responseJson[0]['symbol'][0]['data'])
	fireExtinguisher.lastInspectionDate = datetime.today()
	fireExtinguisher.save()
	newData = InspectionDateList(fireExtinguisher = fireExtinguisher, inspector = request.user)
	newData.save()
	return index(request)
