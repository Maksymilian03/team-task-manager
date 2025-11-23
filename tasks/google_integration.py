from django.conf import settings
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .models import GoogleCredentials

def get_user_google_credentials(user):
    try:
        obj = user.google_credentials
    except GoogleCredentials.DoesNotExist:
        return None

    return Credentials.from_authorized_user_info(obj.credentials_json)

def get_calendar_service(user):
    creds = get_user_google_credentials(user)
    if not creds:
        return None
    # refresh tokenów, jeśli wygasły – google-auth robi to automatycznie,
    # ale w razie czego można dodać ręczną obsługę expiry.
    return build("calendar", "v3", credentials=creds)
