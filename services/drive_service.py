import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
import io
from config import SERVICE_ACCOUNT_KEY

def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY, scopes=['https://www.googleapis.com/auth/drive'])
    return build('drive', 'v3', credentials=credentials)

def list_files(mime_type=None):
    service = get_drive_service()
    query = f"mimeType='{mime_type}'" if mime_type else None
    results = service.files().list(q=query, pageSize=10, fields="files(id, name)").execute()
    return results.get('files', [])

def download_file(file_id, file_name):
    os.makedirs("temp", exist_ok=True)  # Crée le dossier temp si nécessaire
    service = get_drive_service()
    try:
        request = service.files().get_media(fileId=file_id)
        file_path = f"temp/{file_name}"
        with io.FileIO(file_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        return file_path
    except HttpError as e:
        print(f"Erreur Drive API: {e}")
        return None
