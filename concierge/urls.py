from django.urls import path

from . import views

app_name = 'concierge'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('api/requests/', views.submit_request, name='submit_request'),
]
