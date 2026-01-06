from google.auth import default
from google.auth.transport.requests import Request
from google.cloud import vision_v1
import os

# 1. Charge les credentials
credentials, project_id = default()

# 2. Vérifie et rafraîchis les credentials si nécessaire
if not credentials.valid:
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    else:
        print("❌ Les credentials ne sont pas valides. Exécute 'gcloud auth application-default login --scopes=openid,https://www.googleapis.com/auth/cloud-platform'.")
        exit(1)

print(f"Projet: {project_id}")
print(f"Credentials valides: {credentials.valid}")
print(f"Scopes: {credentials.scopes}")

# 3. Teste avec une vraie image
image_path = "test_image.jpg"  # Remplace par le chemin d'une vraie image dans ton projet

if not os.path.exists(image_path):
    print(f"❌ Le fichier '{image_path}' n'existe pas. Place une image dans le dossier du projet.")
    exit(1)

try:
    client = vision_v1.ImageAnnotatorClient(credentials=credentials)

    with open(image_path, "rb") as image_file:
        content = image_file.read()

    image = vision_v1.Image(content=content)
    response = client.text_detection(image=image)

    if response.error.message:
        print(f"Erreur Vision API: {response.error.message}")
    else:
        print("✅ Texte détecté :")
        print(response.full_text_annotation.text)

except Exception as e:
    print(f"❌ Erreur: {e}")
