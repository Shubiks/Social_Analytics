import datetime
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.exceptions import GoogleAuthError
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from google.auth.transport.requests import Request
from authapp.views import credentials_to_dict

logger = logging.getLogger(__name__)

def youtube_analytics(request):
    """Fetch and return YouTube analytics data"""

    credentials_dict = request.session.get('credentials')

    if not credentials_dict:
        return redirect(reverse("google_login"))

    try:
        credentials = Credentials(**credentials_dict)

        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            request.session["credentials"] = credentials_to_dict(credentials)

        youtube = build("youtube", "v3", credentials=credentials)
        youtube_analytics = build("youtubeAnalytics", "v2", credentials=credentials)

        # Get authenticated user's channel ID
        channel_response = youtube.channels().list(part="id", mine=True).execute()
        channel_id = channel_response["items"][0]["id"] if channel_response.get("items") else None

        if not channel_id:
            return JsonResponse({"error": "Could not retrieve channel ID"}, status=400)

        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=30)

        def fetch_report(metrics, dimensions):
            try:
                return youtube_analytics.reports().query(
                    ids=f"channel=={channel_id}",
                    startDate=start_date.strftime("%Y-%m-%d"),
                    endDate=end_date.strftime("%Y-%m-%d"),
                    metrics=metrics,
                    dimensions=dimensions,
                ).execute()
            except Exception as e:
                logger.error(f"Error fetching report: {e}")
                return None

        # Fetch Audience Data
        age_distribution = fetch_report("viewerPercentage", "ageGroup")
        gender_distribution = fetch_report("viewerPercentage", "gender")
        top_location = fetch_report("views", "country")

        # Fetch Channel Performance Over Time
        views_over_time = fetch_report("views", "day")
        watch_time_over_time = fetch_report("estimatedMinutesWatched", "day")
        new_subscribers_over_time = fetch_report("subscribersGained", "day")

        # Fetch Performance Metrics
        avg_view_duration = fetch_report("averageViewDuration", "day")
        ctr = fetch_report("cardClickRate", "day")
        avg_retention_rate = fetch_report("averageViewPercentage", "day")

        # Fetch Video Performance
        views_per_video = fetch_report("views", "")
        likes_per_video = fetch_report("likes", "")
        comments_per_video = fetch_report("comments", "")
        shares_per_video = fetch_report("shares", "")

        # Get video details
        video_ids = []
        request_video = youtube.search().list(
            part="snippet",
            forMine=True,
            type="video",
            maxResults=50
        )
        response_video = request_video.execute()

        video_details = {}
        for item in response_video.get("items", []):
            video_id = item["id"]["videoId"]
            video_ids.append(video_id)
            video_details[video_id] = item["snippet"]

        # Combine all results
        response_data = {
            "audience": {
                "age_distribution": age_distribution,
                "gender_distribution": gender_distribution,
                "top_location": top_location
            },
            "channel_performance": {
                "views_over_time": views_over_time,
                "watch_time_over_time": watch_time_over_time,
                "new_subscribers_over_time": new_subscribers_over_time
            },
            "performance_metrics": {
                "average_view_duration": avg_view_duration,
                "click_through_rate": ctr,
                "average_retention_rate": avg_retention_rate
            },
            "video_performance": {
                "views_per_video": views_per_video,
                "likes_per_video": likes_per_video
            },
            "user_interaction": {
                "comments_per_video": comments_per_video,
                "shares_per_video": shares_per_video
            },
            "video_details": video_details,  # adding video details to response.
        }

        return JsonResponse(response_data)

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

    analytics = {}
    if video_ids:
        analytics = {video_id: get_video_details(video_id) for video_id in video_ids}

    return JsonResponse({"channel_info": channel_info, "analytics": analytics})