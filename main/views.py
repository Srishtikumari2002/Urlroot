from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Urlroot
import string
import random
import requests
import json
from django.urls import reverse_lazy
from .forms import SignupForm
from django.views import generic

import imageio
import environ
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.face.models import TrainingStatusType

# Create your views here.

env = environ.Env()
environ.Env.read_env()


def index(request):
    """View function for the home page of Urlroot."""
    # if user is logged in then show them their dashboard

    if request.user.is_authenticated:
        return dashboard(request)

    # else home page of the website
    return render(request, 'index.html')

@login_required
def dashboard(request):
    """View function for user dashboard."""

    qry = Urlroot.objects.all().filter(creator=request.user)
    context = {}
    if qry.exists():
        short_urls = []
        for i in range(len(qry)):
            short_urls.append((qry[i].link, qry[i].short, qry[i].published))

        context["short_urls"] = short_urls

    else:
        context["short_urls"] =  "none"

    return render(request, 'dashboard.html', context=context)

def docs(request):
    return render(request, 'docs.html')

@login_required
def url_edit(request, short):
    qry = Urlroot.objects.all().filter(short=short, creator=request.user)

    if qry.exists():
        data = qry.first()
        context = {
            'id':data.id,
            'short': data.short,
            'link': data.link,
            'message': data.message
        }
        return render(request, 'url_edit.html', context=context)

    return redirect(index)

@login_required
def check_short(request):
    if(request.method=='GET'):
        short=request.GET.get("short")
        if len(short) == 0:
            return JsonResponse({'empty':'True'},status=200)
        qry=Urlroot.objects.all().filter(short=short)
        if(qry.exists()):
            return  JsonResponse({'exists':'True', 'empty':'False'},status=200)
        else:
            return JsonResponse({'exists': 'False','empty':'False'}, status=200)

@login_required
def save_custom_backhalf(request):
    if(request.method=='POST'):
        id=request.POST.get("shortid")
        short = request.POST.get('short')
        message = request.POST.get('message')
        
        qry=Urlroot.objects.all().filter(id=id)

        if(qry.exists()):
            qry = qry.first()
            qry.short = short
            qry.message = message
            qry.save()
            return JsonResponse({'status':'ok'},status=200)
        
    return  JsonResponse({'status':'failed'},status=200)

@login_required
def create_new_short(request):
    if request.method == 'POST':

        link = request.POST.get('link')
        
        chars = string.ascii_uppercase + string.digits + string.ascii_lowercase

        short = ''.join(random.choice(chars) for _ in range(8))

        qry = Urlroot.objects.all().filter(short=short)
        
        while qry.exists():
            short = ''.join(random.choice(chars) for _ in range(8))
            qry = Urlroot.objects.all().filter(short=short)
        
        try:
            Urlroot(link=link, short=short, creator=request.user).save()
            return redirect(url_edit, short)
        except Exception as e:
            print(e)
            return redirect(index)
        
def view_short(request, short):

    qry = Urlroot.objects.all().filter(short=short)

    if qry.exists():
        data = qry.first()
        API_KEY = 'AIzaSyCETQG_Ijd-E7HGjEzATCexcjYkcyrCBjI'
        url = 'https://safebrowsing.googleapis.com/v4/threatMatches:find?key={}'.format(API_KEY)
        payload = ("""{
            "client": {
                "clientId":"urlroot",
                "clientVersion":"1.5.2"
                },
            "threatInfo": {
                "threatTypes":["MALWARE", "SOCIAL_ENGINEERING"],
                "platformTypes":["ALL_PLATFORMS"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [
                    {"url": "%s"},
                ]
            }
        }""" % data.link)
        headers = {
            'Content-Type': 'text/plain'
            }

        response = requests.request("POST",url, headers=headers, data=payload )
        response = json.loads(response.text)

        if 'matches' in response.keys():
            secure = 'False'
        else:
            secure = 'True'

        context = {
            'link': data.link,
            'secure': secure,
            'message': data.message,
            'short': data.short
        }
        return render(request, 'view_short.html', context=context)

    return redirect(index)

# admin signup

def create_face_id(username):

    KEY = env("KEY")

    ENDPOINT = env("ENDPOINT")

    PERSON_GROUP_ID = 'urlrootstaff'
    
    face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))

    if PERSON_GROUP_ID not in [x.person_group_id for x in face_client.person_group.list()]:
        face_client.person_group.create(person_group_id=PERSON_GROUP_ID, name=PERSON_GROUP_ID)

    staff = face_client.person_group_person.create(person_group_id=PERSON_GROUP_ID, name=username)

    video  = imageio.get_reader('face.avi',  'ffmpeg')

    for i, im in enumerate(video):
        if i>=8:
            break
        
        imageio.imwrite('temp.jpg', im)

        face_client.person_group_person.add_face_from_stream(PERSON_GROUP_ID, staff.person_id, open('temp.jpg', 'r+b'))

    
    face_client.person_group.train(PERSON_GROUP_ID)

    while True:
        training_status = face_client.person_group.get_training_status(PERSON_GROUP_ID)
        if (training_status.status is TrainingStatusType.succeeded):
            break
        elif (training_status.status is TrainingStatusType.failed):
            face_client.person_group.delete(person_group_id=PERSON_GROUP_ID)
            # return 0 for "Error registering face."
            return 0
    # return 1 for "Success"        
    return 1

class AdminSignup(generic.CreateView):
    form_class = SignupForm
    success_url = reverse_lazy("admin:login")
    template_name = "admin/signup.html"
    
    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        file = request.FILES.get('file')
        
        if file != None:
            with open('face.avi', 'wb+') as f:
                for chunk in file.chunks():
                    f.write(chunk)
            face_response = create_face_id(username = request.POST.get('username'))

            if not face_response:
                return self.form_invalid(form)

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)