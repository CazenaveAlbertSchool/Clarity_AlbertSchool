import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-insecure")
    DEBUG = os.getenv("DEBUG", "False") == "True"

    # Google Cloud
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    BUCKET_NAME = os.getenv("BUCKET_NAME")
    PROJECT_ID = os.getenv("PROJECT_ID")

    # Rappels
    REMINDER_DAYS_BEFORE = int(os.getenv("REMINDER_DAYS_BEFORE", 90))
    CALENDAR_TIMEZONE = os.getenv("CALENDAR_TIMEZONE", "Europe/Paris")

    # Modèles ML
    MODEL_PATH = "models/document_classifier.joblib"
    VECTORIZER_PATH = "models/tfidf_vectorizer.joblib"
