# analytics_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('youtube-analytics/', views.youtube_analytics, name='youtube_analytics'),
    path('channel/<str:handle>/', views.youtube_data_api, name='youtube_data_api'),
    # Add other URL patterns as needed for your analytics app
]