import os
from dotenv import load_dotenv

# Charge les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration Google Cloud
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
LOCATION = os.getenv('GOOGLE_CLOUD_LOCATION', 'eu-west1')
SERVICE_ACCOUNT_KEY = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
DOCUMENTAI_PROCESSOR_ID = os.getenv('DOCUMENTAI_PROCESSOR_ID')
BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'cyprien-documents-bucket')
