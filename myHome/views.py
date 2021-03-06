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
import math
# Create your views here.

def index(request):
	return render(request, "index.html")

def list(request, *args, **kwargs):
	if request.user.is_authenticated :
		user = request.user
		userList = User.objects.all()
		getSearchType = request.GET.get('searchtype','')	
		getSearch = request.GET.get('search','')
		getMode = request.GET.get('mode','')
		getSort = request.GET.get('sort','')	
		getFireExtinguisher = request.GET.getlist('fireextinguisher','')
		if request.GET.get('pagenumber',''):
			pageNumber = request.GET['pagenumber']	
		else:
			pageNumber = 1
		if getMode == 'add':
			return addfireextinguisher(request) 
		elif getMode == 'delete':
			fireExtinguisherList = FireExtinguisherList.objects.filter(id__in = getFireExtinguisher)
			fireExtinguisherList.delete()
		if getMode != 'delete' and getFireExtinguisher != '':
			fireExtinguisherList = FireExtinguisherList.objects.filter(id__in = getFireExtinguisher)
		else :
			if getSearchType == "place":
				fireExtinguisherList = FireExtinguisherList.objects.filter(place__icontains = getSearch)
			elif getSearchType == "mainInspector":
				fireExtinguisherList = FireExtinguisherList.objects.filter(mainInspector__name__icontains = getSearch)
			else :
				fireExtinguisherList = FireExtinguisherList.objects.all()
		if user.company != 'AD':
			fireExtinguisherList = fireExtinguisherList.filter(company = user.company)
		if getSort:
			fireExtinguisherList = fireExtinguisherList.order_by(getSort)
		else:
			fireExtinguisherList = fireExtinguisherList.order_by("place")
		pageSize = 20
		maxPageNumber = int(fireExtinguisherList.count()/pageSize)
		if fireExtinguisherList.count()%pageSize:
			maxPageNumber = maxPageNumber + 1;
		if maxPageNumber == 0:
			maxPageNumber = 1	
		if int(pageNumber) > maxPageNumber:
			pageNumber = maxPageNumber
		minIdx = (int(pageNumber)-1)*pageSize
		maxIdx = minIdx + pageSize
		if maxIdx > fireExtinguisherList.count():
			maxIdx = fireExtinguisherList.count()
		fireExtinguisherList = fireExtinguisherList[minIdx:maxIdx]
		context = {"fireExtinguisherList" : fireExtinguisherList, "userList" : userList, "search" : getSearch, "pageNumber" : pageNumber, "maxPageNumber" : maxPageNumber, "sortType" : getSort}
		if getMode == 'qr':
			return render(request, "qrlist.html", context)
		return render(request, "list.html", context)
	else :
		return redirect("/index")

def addfireextinguisher(request, *args, **kwargs):
	if request.user.is_authenticated:
		if request.user.is_admin:
			userList = User.objects.all()
			if request.method == "POST":
				if FireExtinguisherList.objects.filter(place = request.POST['place']).count() != 0:
					context = {"user" : request.user, "userList" : userList, "error" : "등록된 장소입니다."}
					return render(request, "addfireextinguisher.html", context)
				elif not request.FILES.get('img',''):
					context = {"user" : request.user, "userList" : userList, "error" : "사진이 없습니다."}
					return render(request, "addfireextinguisher.html", context)
				else :
					newData = FireExtinguisherList(place = request.POST['place'], company = request.POST['company'], lastInspectionDate = request.POST['lastinspectiondate'], mainInspector = User.objects.get(serviceNumber = request.POST['maininspector']), image = request.FILES['img'])
					newData.save()
					return redirect("/list")	
			else:
				context = {"user" : request.user, "userList" : userList}
				return render(request, "addfireextinguisher.html", context)
	return redirect("/index")

def updatefireextinguisher(request, *args, **kwargs):
	if not request.user.is_admin :
		return redirect("/index")
	if request.method == "POST":
		fireExtinguisher = FireExtinguisherList.objects.get(id = request.POST['id'])
		fireExtinguisher.place = request.POST['place']
		fireExtinguisher.mainInspector = User.objects.get(serviceNumber = request.POST['mainInspector'])
		fireExtinguisher.update()
		return redirect("/index")	
	else :
		fireExtinguisher = FireExtinguisherList.objects.get(id = request.GET['id'])
		context = {"fireExtinguisher" : fireExtinguisher, "userList" : User.objects.all()}	
		return render(request, "updatefireextinguisher.html", context)

def inspectionlist(request, *args, **kwargs):
	if request.user.is_authenticated :
		user = request.user
		userList = User.objects.all()
		getSearchType = request.GET.get('searchtype','')
		getSearch = request.GET.get('search','')
		getInspectionDate = request.GET.getlist('inspectiondate','')
		if request.GET.get('pagenumber',''):
			pageNumber = request.GET['pagenumber']	
		else:
			pageNumber = 1
		if request.GET.get('delete','') != '' and getInspectionDate is not None:
			inspectionDateList = InspectionDateList.objects.filter(id__in = getInspectionDate)
			inspectionDateList.delete()	
		inspectionDateList = InspectionDateList.objects.all().order_by("-inspectionDate")
		if request.GET.get('start',''):
			inspectionDateList = inspectionDateList.filter(inspectionDate__date__range=(request.GET['start'],request.GET['end']))
		if getSearch:	
			if getSearchType == 'place' :
				inspectionDateList = inspectionDateList.filter(fireExtinguisher__place__icontains = getSearch)
			elif getSearchType == 'mainInspector':
				inspectionDateList = inspectionDateList.filter(inspector__name__icontains = getSearch)
		if user.company != 'AD':
			inspectionDateList = inspectionDateList.filter(fireExtinguisher__company = user.company)
		pageSize = 20
		maxPageNumber = int(inspectionDateList.count()/pageSize)
		if inspectionDateList.count()%pageSize:
			maxPageNumber = maxPageNumber + 1
		if maxPageNumber == 0:
			maxPageNumber = 1
		if int(pageNumber) > maxPageNumber:
			pageNumber = maxPageNumber
		minIdx = (int(pageNumber)-1)*pageSize
		maxIdx = minIdx + pageSize
		if maxIdx > inspectionDateList.count():
			maxIdx = inspectionDateList.count()
		inspectionDateList = inspectionDateList[minIdx:maxIdx]
		context = {"inspectionDateList" : inspectionDateList, "userList" : userList, "search" : getSearch, "pageNumber" : pageNumber, "maxPageNumber" : maxPageNumber}
		return render(request, "inspectionlist.html", context)
	else :
		return redirect("/index")

def updateinspectiondate(request, pk):
	if not request.user.is_admin:
		return redirect("/index")
	try:
		inspectionDate = InspectionDateList.objects.get(id = pk)
		inspectionDate.action = request.POST.get('action','')
		inspectionDate.save()
		return redirect("/inspectionlist")
	except:
		return redirect("/index")
	
def userlist(request):
	if request.user.is_authenticated :
		if not request.user.is_admin :
			return redirect("/index")
		user = request.user
		userList = User.objects.all()
		if request.GET.get('search','') :
			getSearch = request.GET['search']
			getSearchType = request.GET['searchtype']
			if getSearchType == 'name':
				userList = userList.filter(name__icontains = getSearch)
			elif getSearchType == 'serviceNumber':
				userList = userList.filter(serviceNumber__icontains = getSearch)
		if request.GET.get('sort','') == '' :
			userList = userList.order_by('serviceNumber')
		else :
			userList = userList.order_by(request.GET.get('sort'))
		if request.GET.get('pageNumber',''):
			pageNumber = request.GET['pageNumber']
		else:
			pageNumber = 1
		pageSize = 20
		maxPageNumber = int(userList.count()/pageSize)
		if userList.count()%pageSize:
			maxPageNumber = maxPageNumber + 1;
		if maxPageNumber == 0:
			maxPageNumber = 1	
		if int(pageNumber) > maxPageNumber:
			pageNumber = maxPageNumber
		minIdx = (int(pageNumber)-1)*pageSize
		maxIdx = minIdx + pageSize
		if maxIdx > userList.count():
			maxIdx = userList.count()
		userList = userList[minIdx:maxIdx]
		context = {"userList" : userList, "pageNumber" : pageNumber, "maxPageNumber" : maxPageNumber}
		return render(request, "userlist.html", context)
	else :
		return index(request)

def updateuser(request):
	if not request.user.is_authenticated :
		return redirect("/index")	
	if request.method == "POST":
		newPassword = request.POST["password1"]
		user = User.objects.get(serviceNumber = request.POST['serviceNumber'])
		originPassword = user.password
		if newPassword != '' :
			if not request.user.is_admin and not check_password(request.POST['originpassword'], originPassword):
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
		user.company = request.POST["company"]
		user.save()
		if request.user.serviceNumber == request.POST["serviceNumber"] :
			auth.login(request, user)
			return redirect("/index")
		return redirect("/userlist")
	else :
		user = User.objects.get(serviceNumber = request.GET.get('serviceNumber',''))
		return render(request, 'updateuser.html', {"User" : user})	

def activeuser(request):
	if not request.user.is_admin :
		return redirect("/index")	
	try:
		user = User.objects.get(serviceNumber = request.GET['serviceNumber'])
		user.is_active = True
		user.save()
	except:
		return redirect("/index")
	return redirect("/userlist")

def deleteuser(request):
	if not request.user.is_authenticated :
		return redirect("/index")	
	User.objects.get(serviceNumber = request.POST['serviceNumber']).delete()
	return redirect("/userlist")

def login(request, *args, **kwargs):
	if request.method == "POST":
		serviceNumber = request.POST['serviceNumber']
		password = request.POST['password']
		user = auth.authenticate(serviceNumber=serviceNumber, password=password)
		if user is not None:
			if user.is_active:
				auth.login(request, user)
				if request.GET.get('next','') == '':
					return redirect("/index")
				else:
					return redirect(request.GET['next'])
			else:
				return render(request, 'login.html', {'serviceNumber':serviceNumber,'password':password,'error':'승인되지 않은 계정'})
		else:
			return render(request, 'login.html', {'serviceNumber':serviceNumber,'password':password,'error':'군번 혹은 비밀번호가 틀렸습니다.'})
	else:
		return render(request, 'login.html')

def logout(request):
	auth.logout(request)
	return redirect("/index") 

def signup(request):
	if request.method == "POST":
		password = request.POST["password1"]
		if User.objects.filter(serviceNumber = request.POST["serviceNumber"]).count() == 1:
			return render(request, 'signup.html', {"error" : " 이미 등록된 군번입니다."})
		if len(password) < 8:
			return render(request, 'signup.html', {"error" : "비밀번호는 8자 이상이어야 합니다."})
		if password == request.POST["password2"]:
			user = User.objects.create_user(
				serviceNumber = request.POST["serviceNumber"],
				name = request.POST["name"],
				company = request.POST["company"],
			)
			user.set_password(password)
			user.save()
			return redirect("/index") 
		return render(request, 'signup.html') 	
	else:
		return render(request, 'signup.html')

def qrreader(request):
	if not request.user.is_authenticated :
		return redirect("/index")
	return render(request, 'qrreader.html')

def qrapi(request):
	if not request.user.is_authenticated :
		return redirect("/index")
	if request.POST['qrdata'] != '' :
		try :
			fireExtinguisher = FireExtinguisherList.objects.get(id = request.POST['qrdata'])
		except :
			return render(request, 'qrreader.html', {'error':'이미지나 값이 틀렸습니다.'})
	else :
		if 'qrimg' not in request.FILES:
			return render(request,'qrreader.html', {'error':'이미지나 값이 필요합니다.'})
		files = {'file':request.FILES['qrimg']}
		img_file = BytesIO(files['file'].read())
		img = Image.open(img_file)
		file_size = request.POST['file-size']
		if(int(file_size) > 1024000):
			ratio = math.sqrt(1024000/float(file_size))
			resize_img = img.resize((int(img.size[0] * ratio ), int(img.size[1] * ratio)))
		else:
			resize_img = img
		buf = BytesIO()
		resize_img.save(buf, format=request.POST['file-type'])
		files = {'file':buf.getvalue()}
		response = requests.post("http://api.qrserver.com/v1/read-qr-code/", data = {"MAX_FILE_SIZE" : "1048576"},  files = files)
		responseJson = response.json()
		if responseJson[0]['symbol'][0]['error'] == "could not find/read QR Code":
			return render(request, 'qrreader.html', {'error' : 'Qr code 인식 안됨'})
		try:	
			fireExtinguisher = FireExtinguisherList.objects.get(id = responseJson[0]['symbol'][0]['data'])
		except (ValueError, FireExtinguisherList.DoesNotExist):
			return render(request, 'qrreader.html', {'error':'이미지나 값이 틀렸습니다.'})
	fireExtinguisher.lastInspectionDate = datetime.today()
	fireExtinguisher.update()
	newData = InspectionDateList(fireExtinguisher = fireExtinguisher, inspector = request.user, result = request.POST['result'])
	newData.save()
	return index(request)
