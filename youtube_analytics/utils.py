import os
import datetime
import isodate
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logger = logging.getLogger(__name__)

# Load API Key securely from environment variables
API_KEY = "AIzaSyDkSXaIBF9ap2QhRCf-yadjsKZGP5zgf-Y"  # Set this in your .env or system environment

if not API_KEY:
    raise ValueError("Missing YOUTUBE_API_KEY in environment variables!")

# Initialize YouTube API Client once
youtube = build("youtube", "v3", developerKey=API_KEY)

def get_channel_id(handle):
    """Fetch YouTube Channel ID from Handle"""
    try:
        request = youtube.channels().list(part="id", forHandle=handle)
        response = request.execute()
        
        if "items" in response and response["items"]:
            return response["items"][0]["id"]
        
        return None
    except HttpError as e:
        logger.error(f"Error fetching channel ID: {e}")
        return None

def get_channel_details(channel_id):
    """Fetch YouTube Channel Details"""
    try:
        request = youtube.channels().list(part="snippet,statistics", id=channel_id)
        response = request.execute()
        
        if "items" in response and response["items"]:
            channel_data = response["items"][0]
            return {
                "channel_name": channel_data["snippet"]["title"],
                "subscribers": channel_data["statistics"].get("subscriberCount", "N/A"),
                "total_videos": channel_data["statistics"].get("videoCount", "N/A"),
                "total_views": channel_data["statistics"].get("viewCount", "N/A"),
            }
        return None
    except HttpError as e:
        logger.error(f"Error fetching channel details: {e}")
        return None

def get_channel_videos(channel_id):
    """Fetch all video IDs from a given channel."""
    video_ids = []
    next_page_token = None

    try:
        while True:
            request = youtube.search().list(
                part="id",
                channelId=channel_id,
                maxResults=50,  # API limit
                order="date",
                type="video",
                pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response.get("items", []):
                video_ids.append(item["id"]["videoId"])

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        return video_ids

    except HttpError as e:
        logger.error(f"Error fetching channel videos: {e}")
        return []

def get_video_details(video_ids):
    """Fetch video statistics & compute watch time, avg views & duration."""
    total_watch_time = 0
    total_views = 0
    total_duration = datetime.timedelta()
    total_videos = len(video_ids)

    try:
        for i in range(0, len(video_ids), 50):  # API allows max 50 per request
            request = youtube.videos().list(
                part="statistics,contentDetails",
                id=",".join(video_ids[i : i + 50])
            )
            response = request.execute()

            for item in response.get("items", []):
                # Parse video duration
                duration = isodate.parse_duration(item["contentDetails"]["duration"])
                total_duration += duration

                views = int(item["statistics"].get("viewCount", 0))
                total_views += views
                avg_watch_time = duration.total_seconds() * views
                total_watch_time += avg_watch_time

        # Convert total watch time from seconds to hours
        total_watch_time_hours = total_watch_time / 3600
        avg_views = total_views / total_videos if total_videos else 0
        avg_duration = total_duration / total_videos if total_videos else datetime.timedelta()

        return {
            "total_watch_time_hours": round(total_watch_time_hours, 2),
            "average_views": round(avg_views, 2),
            "average_video_duration": str(avg_duration)
        }

    except HttpError as e:
        logger.error(f"Error fetching video details: {e}")
        return {}
