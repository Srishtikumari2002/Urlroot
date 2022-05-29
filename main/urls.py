from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('urlroot-documentation/', views.docs, name='docs'),
    path('<str:short>/edit/', views.url_edit, name='url_edit'),
    path('create-new-short-url/', views.create_new_short, name='create_short'),
    path('<str:short>/', views.view_short, name="view_short"),
    path('check-for-user-created-shorts-existence', views.check_short, name="check_short"),
    path('save-custom-backhalf', views.save_custom_backhalf, name="save_custom_backhalf"),
]