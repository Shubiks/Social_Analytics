from django.urls import path
from .views import youtube_analytics,youtube_data_api

urlpatterns = [
    path('channel/<str:channel_id>/', youtube_analytics, name='youtube_channel_data'),
    path("general/<str:handle>/", youtube_data_api, name="youtube-data"),
]
