import os
from dotenv import load_dotenv
from google.auth import default

# Charge les variables d'environnement depuis le fichier .env
load_dotenv()

USE_GCLOUD_AUTH = os.getenv('USE_GCLOUD_AUTH', 'false').lower() == 'true'

if USE_GCLOUD_AUTH:
    credentials, PROJECT_ID = default()
else:
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')

LOCATION = os.getenv('GOOGLE_CLOUD_LOCATION', 'eu-west1')
DOCUMENTAI_PROCESSOR_ID = os.getenv('DOCUMENTAI_PROCESSOR_ID')
BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'clarity-documents-bucket')

# Variables pour les notifications (optionnelles)
# SENDER_EMAIL: Adresse email de l'expéditeur (utilisée pour Gmail API)
# RECIPIENT_EMAIL: Adresse email du destinataire (par défaut, utilise SENDER_EMAIL)
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

# Variables pour le client JS Google (Drive)
# GOOGLE_API_KEY: clé API pour le SDK JS (publique, mais à ne pas commiter)
# GOOGLE_CLIENT_ID: client OAuth 2.0 pour Drive (gapi)
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')