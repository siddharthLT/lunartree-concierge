from django.urls import path

from . import views

app_name = 'concierge'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('ddf-intel/', views.ddf_intel, name='ddf_intel'),
    path('api/requests/', views.submit_request, name='submit_request'),
]
