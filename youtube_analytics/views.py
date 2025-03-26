from django.shortcuts import render
from django.http import JsonResponse
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.exceptions import GoogleAuthError
import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

def youtube_analytics(request,channel_id):
    """Fetch and return YouTube analytics data"""

    # Retrieve credentials from session
    credentials_dict = request.session.get('credentials')

    if not credentials_dict:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    try:
        # Convert dictionary to Credentials object
        credentials = Credentials(**credentials_dict)

        # Check if credentials are valid
        if credentials.expired:
            return JsonResponse({"error": "Credentials expired. Please reauthenticate."}, status=401)

        # Initialize YouTube Analytics API client
        youtube_analytics = build("youtubeAnalytics", "v2", credentials=credentials)

        # Calculate last 30 days dynamically
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=30)

        # Fetch analytics data
        response = youtube_analytics.reports().query(
            ids="channel==MINE",
            startDate=start_date.strftime("%Y-%m-%d"),
            endDate=end_date.strftime("%Y-%m-%d"),
            metrics="views,likes,subscribersGained",
            dimensions="day"
        ).execute()

        return JsonResponse(response)

    except GoogleAuthError as auth_error:
        logger.error(f"Google Authentication Error: {auth_error}")
        return JsonResponse({"error": "Google authentication failed."}, status=401)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JsonResponse({"error": "Internal server error."}, status=500)


from django.http import JsonResponse
from .utils import get_channel_id, get_channel_details, get_channel_videos, get_video_details

def youtube_data_api(request, handle):
    """API to fetch YouTube data dynamically"""
    channel_id = get_channel_id(handle)
    if not channel_id:
        return JsonResponse({"error": "Invalid YouTube handle"}, status=404)

    channel_info = get_channel_details(channel_id)
    video_ids = get_channel_videos(channel_id)
    analytics = get_video_details(video_ids) if video_ids else {}

    return JsonResponse({"channel_info": channel_info, "analytics": analytics})
