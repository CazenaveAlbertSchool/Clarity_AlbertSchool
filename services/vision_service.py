from google.cloud import vision_v1
from google.cloud.vision_v1 import types, ImageAnnotatorClient
from google.api_core.exceptions import GoogleAPICallError, RetryError

def detect_text(file_path):
    try:
        client = ImageAnnotatorClient()
        with open(file_path, 'rb') as image_file:
            content = image_file.read()
        image = types.Image(content=content)
        # Optionnel : forcer la langue (ex. français)
        image_context = types.ImageContext(language_hints=["fr"])
        response = client.text_detection(image=image, image_context=image_context)
        if response.error.message:
            raise Exception(f"Vision API error: {response.error.message}")
        return response.full_text_annotation.text
    except (GoogleAPICallError, RetryError, Exception) as e:
        print(f"Erreur lors de l'OCR: {e}")
        return None
