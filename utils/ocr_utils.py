import re
from datetime import datetime
import joblib
from google.cloud import vision
from config import Config
import logging

logger = logging.getLogger(__name__)

def extract_text_from_image(image_uri):
    """
    Extrait le texte d'une image/PDF via Google Vision API.
    Args:
        image_uri (str): URI du fichier dans Google Cloud Storage (ex: gs://bucket/filename).
    Returns:
        str: Texte extrait, ou None en cas d'erreur.
    """
    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(source=vision.ImageSource(image_uri=image_uri))
        response = client.text_detection(image=image)
        if response.error.message:
            logger.error(f"Erreur Vision API: {response.error.message}")
            return None
        return response.full_text_annotation.text if response.full_text_annotation else None
    except Exception as e:
        logger.error(f"Erreur lors de l'OCR: {e}")
        return None

def extract_expiry_date(text):
    """
    Extrait une date d'expiration depuis un texte (format JJ/MM/AAAA ou JJ-MM-AAAA).
    Args:
        text (str): Texte dans lequel chercher la date.
    Returns:
        datetime: Objet date, ou None si aucune date valide n'est trouvée.
    """
    if not text:
        return None

    # Recherche des dates au format JJ/MM/AAAA ou JJ-MM-AAAA
    date_pattern = r"\b\d{2}[/-]\d{2}[/-]\d{4}\b"
    dates = re.findall(date_pattern, text)

    if not dates:
        return None

    # Essayer les formats possibles
    for date_str in dates:
        for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
    return None

def classify_document(text):
    """
    Classifie un document en utilisant le modèle ML pré-entraîné.
    Args:
        text (str): Texte à classifier.
    Returns:
        str: Label prédit (ex: "passeport").
    """
    try:
        vectorizer = joblib.load(Config.VECTORIZER_PATH)
        model = joblib.load(Config.MODEL_PATH)
        text_vectorized = vectorizer.transform([text])
        return model.predict(text_vectorized)[0]
    except Exception as e:
        logger.error(f"Erreur lors de la classification: {e}")
        return "inconnu"
