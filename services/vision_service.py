from google.cloud import vision_v1
from google.cloud.vision_v1 import ImageAnnotatorClient, types
from google.auth import default
from google.api_core.exceptions import GoogleAPICallError, RetryError

def detect_text(file_path):
    try:
        # Utilise l'authentification par défaut (gcloud)
        credentials, _ = default()

        # Initialise le client Vision API avec les credentials
        client = ImageAnnotatorClient(credentials=credentials)

        with open(file_path, 'rb') as image_file:
            content = image_file.read()

        image = types.Image(content=content)

        # Optionnel : forcer la détection en français
        image_context = types.ImageContext(language_hints=["fr"])

        # Appel à l'API Vision pour la détection de texte
        response = client.text_detection(
            image=image,
            image_context=image_context
        )

        # Vérifie les erreurs dans la réponse
        if response.error.message:
            raise Exception(f"Vision API error: {response.error.message}")

        # Retourne le texte extrait
        return response.full_text_annotation.text

    except (GoogleAPICallError, RetryError, IOError, Exception) as e:
        print(f"Erreur lors de l'OCR: {e}")
        return None
