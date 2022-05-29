from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django import forms
import environ

import imageio
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials

env = environ.Env()
environ.Env.read_env()

class SignupForm(UserCreationForm):
    file = forms.FileField()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_staff =  True
        # Admin can only be created by other admins
        # this form creates staff who can log in to the admin panel
        # but can't edit or view anything until given access by the admin
        user.is_superuser = False
        if commit:
            user.save()
        return user

def detect_face(username):
    KEY = env("KEY")

    ENDPOINT = env("ENDPOINT")

    PERSON_GROUP_ID = 'urlrootstaff'
    
    face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))

    video  = imageio.get_reader('face.avi',  'ffmpeg')

    detection = []

    for i, im in enumerate(video):
        if i>=3:
            break

        imageio.imwrite('temp.jpg', im)
        
        face_ids = []
        faces = face_client.face.detect_with_stream(open('temp.jpg', 'r+b'), detection_model='detection_03')

        for face in faces:
            face_ids.append(face.face_id)
    
        results = face_client.face.identify(face_ids, PERSON_GROUP_ID)

        if not results:
            detection.append(0)
        
        for person in results:
            if len(person.candidates) > 0:
                personData = face_client.person_group_person.get(PERSON_GROUP_ID, person.candidates[0].person_id)
                if personData.name == username:
                    detection.append(1)
            else:
                detection.append(0)
    
    if len(detection) == 0:
        return False

    elif detection.count(1)/len(detection) > 0.6:
        # face matches with the username
        return True
    else:
        return False


class LoginForm(AuthenticationForm):
  
    file = forms.FileField()
    
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": _(
            "Please enter the correct %(username)s and password for a staff "
            "account. Please be in proper lighting for face recognition."
            "Note that both fields may be case-sensitive."
        ),
    }

    required_css_class = "required"
    def __init__(self, request, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        file = request.FILES.get('file')
        
        if file != None:
            with open('face.avi', 'wb+') as f:
                for chunk in file.chunks():
                    f.write(chunk)


    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        print(detect_face(user.username))
        if (not user.is_staff) or (not detect_face(user.username)):
            raise ValidationError(
                self.error_messages["invalid_login"],
                code="invalid_login",
                params={"username": self.username_field.verbose_name},
            )