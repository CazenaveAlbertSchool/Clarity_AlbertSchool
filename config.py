
import os

# Configuration Google Cloud
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
LOCATION = os.getenv('GOOGLE_CLOUD_LOCATION', 'eu-west1')
BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'cyprien-documents-bucket')

# Chemins des clés (à remplacer par tes fichiers)
SERVICE_ACCOUNT_KEY = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'service-account-key.json')

# ID des processeurs Document AI (à configurer)
DOCUMENTAI_PROCESSOR_ID = os.getenv('DOCUMENTAI_PROCESSOR_ID', 'your-processor-id')
