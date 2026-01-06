
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
from config import SERVICE_ACCOUNT_KEY

def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY)
    return build('drive', 'v3', credentials=credentials)

def list_files():
    service = get_drive_service()
    results = service.files().list(pageSize=10, fields="files(id, name)").execute()
    return results.get('files', [])

def download_file(file_id, file_name):
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(f"temp/{file_name}", 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    return f"temp/{file_name}"
