from django.urls import path

from . import views

app_name = 'concierge'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('welcome/', views.welcome, name='welcome'),
    path('api/welcome/search/', views.welcome_search, name='welcome_search'),
    path('api/welcome/person/<str:pid>/', views.welcome_person, name='welcome_person'),
    path('api/welcome/save/', views.welcome_save, name='welcome_save'),
    path('api/welcome/restore/', views.welcome_restore, name='welcome_restore'),
    path('ddf-intel/', views.ddf_intel, name='ddf_intel'),
    path('experience-biolens/', views.experience_biolens, name='experience_biolens'),
    path('api/attendees/', views.attendees_api, name='attendees'),
    path('api/search-interest/', views.search_interest, name='search_interest'),
    path('api/requests/', views.submit_request, name='submit_request'),
]
