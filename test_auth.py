from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import vision_v1

try:
    credentials, project_id = default()
    print(f"Projet: {project_id}")
    print(f"Credentials valides: {credentials.valid}")
    print(f"Scopes: {credentials.scopes}")  # Affiche les scopes associés

    # Teste la création d'un client Vision API
    client = vision_v1.ImageAnnotatorClient(credentials=credentials)
    print("✅ Client Vision API créé avec succès !")

    # Teste une requête simple
    image = vision_v1.Image()
    response = client.label_detection(image=image)  # Requête test (peut échouer, mais vérifie les permissions)
    print("✅ Requête test effectuée !")

except Exception as e:
    print(f"❌ Erreur: {e}")
