import json
import os
from django.shortcuts import redirect, render
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Convert Credentials to Dictionary
def credentials_to_dict(credentials):
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }

# Step 1: Redirect user to Google's OAuth consent page
def google_login(request):
    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_CLIENT_SECRET_FILE,
        scopes=settings.GOOGLE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    return redirect(auth_url)

# Step 2: Handle OAuth callback & store access token
def google_callback(request):
    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_CLIENT_SECRET_FILE,
        scopes=settings.GOOGLE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials
    request.session["credentials"] = credentials_to_dict(credentials)

    return redirect(reverse("youtube_analytics"))  # Redirect to analytics page

# Step 3: Fetch YouTube Analytics data
def youtube_analytics(request):
    credentials_dict = request.session.get("credentials")

    if not credentials_dict:
        return redirect(reverse("google_login"))

    try:
        # Convert session-stored credentials back to a Credentials object
        credentials = Credentials(**credentials_dict)

        # If credentials are expired, refresh them
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

            # Update session with new credentials
            request.session["credentials"] = credentials_to_dict(credentials)

        youtube_analytics = build("youtubeAnalytics", "v2", credentials=credentials)

        # Fetch views, watch time, and subscribers gained for the channel
        response = youtube_analytics.reports().query(
            ids="channel==MINE",
            startDate="2024-01-01",
            endDate="2025-03-26",
            metrics="views,estimatedMinutesWatched,subscribersGained",
            dimensions="day",
            sort="day"
        ).execute()

        return JsonResponse(response)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
