
from google.cloud import vision_v1
from google.cloud.vision_v1 import types

def detect_text(file_path):
    client = vision_v1.ImageAnnotatorClient()
    with open(file_path, 'rb') as image_file:
        content = image_file.read()
    image = types.Image(content=content)
    response = client.text_detection(image=image)
    return response.full_text_annotation.text
