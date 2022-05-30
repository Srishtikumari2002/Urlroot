from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django import forms
import environ

import imageio
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.face.models import TrainingStatusType

env = environ.Env()
environ.Env.read_env()

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

        try:
            face_client.person_group_person.add_face_from_stream(PERSON_GROUP_ID, staff.person_id, open('temp.jpg', 'r+b'))
        except Exception as e:
            return False

    face_client.person_group.train(PERSON_GROUP_ID)

    while True:
        training_status = face_client.person_group.get_training_status(PERSON_GROUP_ID)
        if (training_status.status is TrainingStatusType.succeeded):
            break
        elif (training_status.status is TrainingStatusType.failed):
            face_client.person_group.delete(person_group_id=PERSON_GROUP_ID)
            # return 0 for "Error registering face."
            return False
    # return 1 for "Success"        
    return True

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
        
        try:
            results = face_client.face.identify(face_ids, PERSON_GROUP_ID)
        except Exception:
            return False

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

class SignupForm(UserCreationForm):
    file = forms.FileField()

    error_messages = {
        **UserCreationForm.error_messages,
        "invalid_face": _(
            "Error detecting face please be in proper lighting for face recognition."
            )
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        face = self.files.get('file')
        try:
            self.username = kwargs.get('data').get('username')
        except Exception:
            print()

        if face != None:
            with open('face.avi', 'wb+') as f:
                for chunk in face.chunks():
                    f.write(chunk)

    def clean_file(self):
        face_response = create_face_id(self.username)
        if not face_response:
            raise ValidationError(
                self.error_messages["invalid_face"],
                code="invalid_face",
            )
        return face_response

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_staff =  True
        user.is_superuser = False
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
  
    file = forms.FileField()
    
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": _(
            "Please enter the correct %(username)s and password for a staff "
            "account. Note that both fields may be case-sensitive."
        ),
        "invalid_face": _(
            "Face doesn't match with %(username)s. If you are the right person "
            "then please be in proper lighting for face recognition."
            )
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
        face_check = detect_face(user.username)
        if (not face_check):
            raise ValidationError(
                self.error_messages["invalid_face"],
                code="invalid_face",
                params={"username": self.username_field.verbose_name},
            )
        if (not user.is_staff):
            raise ValidationError(
                self.error_messages["invalid_login"],
                code="invalid_login",
                params={"username": self.username_field.verbose_name},
            )
