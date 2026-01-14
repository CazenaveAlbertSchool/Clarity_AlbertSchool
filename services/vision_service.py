# vision_service.py
from google.cloud import vision_v1
from google.cloud.vision_v1 import ImageAnnotatorClient, types
from google.auth import default
from google.api_core.exceptions import GoogleAPICallError, RetryError
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_text(file_path):
    try:
        # Force l'utilisation des credentials par défaut (gcloud auth)
        credentials, project_id = default()
        logger.info(f"Projet Google Cloud: {project_id}")
        logger.info(f"Credentials valides: {credentials.valid}")

        # Initialise le client avec les credentials explicites
        client = ImageAnnotatorClient(credentials=credentials)

        with open(file_path, 'rb') as image_file:
            content = image_file.read()

        image = types.Image(content=content)
        image_context = types.ImageContext(language_hints=["fr"])  # Pour le français

        response = client.text_detection(image=image, image_context=image_context)

        if response.error.message:
            logger.error(f"Vision API error: {response.error.message}")
            return None

        return response.full_text_annotation.text

    except (GoogleAPICallError, RetryError, Exception) as e:
        logger.error(f"Erreur lors de l'OCR: {e}", exc_info=True)
        return None
