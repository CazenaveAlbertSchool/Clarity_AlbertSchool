import os
import logging
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from werkzeug.utils import secure_filename
from google.cloud import vision, storage, firestore
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import Config
from utils.ocr_utils import extract_text_from_image, extract_expiry_date, classify_document
from utils.calendar_utils import create_calendar_event

# Configuration de l'application
app = Flask(__name__)
app.config.from_object(Config)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialisation des clients Google Cloud
try:
    credentials = service_account.Credentials.from_service_account_file(
        Config.GOOGLE_APPLICATION_CREDENTIALS
    )
    vision_client = vision.ImageAnnotatorClient(credentials=credentials)
    storage_client = storage.Client(credentials=credentials)
    firestore_client = firestore.Client(credentials=credentials)
    logger.info("Clients Google Cloud initialisés avec succès.")
except Exception as e:
    logger.error(f"Erreur lors de l'initialisation des clients Google Cloud: {e}")
    raise

# Vérifier que les modèles ML existent
if not os.path.exists(Config.MODEL_PATH) or not os.path.exists(Config.VECTORIZER_PATH):
    logger.error(f"Modèles ML manquants. Exécutez d'abord train_model.py.")
    raise FileNotFoundError("Modèles ML introuvables. Veuillez les générer avec train_model.py.")

# Extensions de fichiers autorisées
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    """Vérifie si le fichier a une extension autorisée."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Route principale : affiche le formulaire d'upload et liste les documents traités.
    """
    if request.method == "POST":
        # 1. Vérifier la présence du fichier
        if 'document' not in request.files:
            flash("Aucun fichier sélectionné.", "error")
            return redirect(request.url)

        file = request.files['document']
        if file.filename == '':
            flash("Aucun fichier sélectionné.", "error")
            return redirect(request.url)

        # 2. Vérifier l'extension du fichier
        if not allowed_file(file.filename):
            flash("Type de fichier non autorisé. Utilisez PDF, PNG, JPG ou JPEG.", "error")
            return redirect(request.url)

        # 3. Sécuriser le nom du fichier
        filename = secure_filename(file.filename)

        try:
            # 4. Upload vers Google Cloud Storage
            blob = storage_client.bucket(Config.BUCKET_NAME).blob(filename)
            blob.upload_from_string(
                file.read(),
                content_type=file.content_type
            )
            logger.info(f"Fichier {filename} uploadé vers GCS.")

            # 5. Traiter avec Vision API (OCR)
            image_uri = f"gs://{Config.BUCKET_NAME}/{filename}"
            text = extract_text_from_image(image_uri)
            if not text:
                flash("Aucun texte détecté dans le document.", "warning")
                return redirect(request.url)

            # 6. Classifier le document
            predicted_label = classify_document(text)
            logger.info(f"Document classé comme : {predicted_label}")

            # 7. Extraire la date d'expiration (si applicable)
            expiry_date = None
            if predicted_label in ['cni', 'passeport', 'permis', 'assurance']:
                expiry_date = extract_expiry_date(text)
                if expiry_date:
                    logger.info(f"Date d'expiration détectée : {expiry_date.strftime('%d/%m/%Y')}")

                    # 8. Créer un rappel dans Google Calendar
                    if predicted_label in ['passeport', 'cni', 'permis']:
                        event_link = create_calendar_event(expiry_date, predicted_label, filename)
                        logger.info(f"Rappel créé : {event_link}")

            # 9. Sauvegarder les métadonnées dans Firestore
            doc_ref = firestore_client.collection("documents").document(filename)
            doc_ref.set({
                "filename": filename,
                "text": text[:500],  # Sauvegarder un extrait pour éviter les gros documents
                "predicted_label": predicted_label,
                "expiry_date": expiry_date.strftime("%d/%m/%Y") if expiry_date else None,
                "status": "processed",
                "created_at": firestore.SERVER_TIMESTAMP,
                "calendar_event": event_link if 'event_link' in locals() else None
            })
            logger.info(f"Métadonnées sauvegardées dans Firestore pour {filename}.")

            flash(f"Document {filename} traité avec succès (Type: {predicted_label})!", "success")

        except Exception as e:
            logger.error(f"Erreur lors du traitement de {filename}: {e}")
            flash(f"Erreur lors du traitement: {str(e)}", "error")

        return redirect(url_for('index'))

    # GET: Afficher la liste des documents
    try:
        documents = []
        for doc in firestore_client.collection("documents").order_by("created_at", direction=firestore.Query.DESCENDING).limit(10).stream():
            doc_data = doc.to_dict()
            doc_data['id'] = doc.id
            documents.append(doc_data)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des documents: {e}")
        documents = []

    return render_template("index.html", documents=documents)

@app.errorhandler(500)
def internal_error(error):
    """Gestion des erreurs internes."""
    logger.error(f"Erreur serveur: {error}")
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
