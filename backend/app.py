import os
import re
import joblib
import io
import json
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from googleapiclient.discovery import build
from google.cloud import vision, language_v1, firestore, storage
from google.oauth2 import service_account
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import datetime, timedelta


# Charger les variables d'environnement
load_dotenv()


def extract_expiry_date(text):
    # Recherche des dates au format JJ/MM/AAAA ou JJ-MM-AAAA
    date_pattern = r"\b\d{2}[/-]\d{2}[/-]\d{4}\b"
    dates = re.findall(date_pattern, text)

    if not dates:
        return None

    # Supposons que la dernière date trouvée est la date d'expiration
    expiry_date_str = dates[-1]

    # Convertir en objet datetime
    try:
        expiry_date = datetime.strptime(expiry_date_str, "%d/%m/%Y")
    except ValueError:
        try:
            expiry_date = datetime.strptime(expiry_date_str, "%d-%m-%Y")
        except ValueError:
            return None

    return expiry_date

def create_calendar_event(expiry_date, document_type, filename):
    # Configurer l'API Google Calendar
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    service_account_info = json.load(open(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")))
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES
    )
    service = build('calendar', 'v3', credentials=credentials)

    # Calculer la date de rappel (ex. : 3 mois avant l'expiration)
    reminder_date = expiry_date - timedelta(days=90)

    event = {
        'summary': f"Rappel : Expiration du {document_type} ({filename})",
        'description': f"Votre {document_type} expire le {expiry_date.strftime('%d/%m/%Y')}. Pensez à le renouveler !",
        'start': {
            'dateTime': reminder_date.strftime("%Y-%m-%dT09:00:00"),
            'timeZone': 'Europe/Paris',
        },
        'end': {
            'dateTime': reminder_date.strftime("%Y-%m-%dT10:00:00"),
            'timeZone': 'Europe/Paris',
        },
        'reminders': {
            'useDefault': True,
        },
    }

    # Créer l'événement dans le calendrier principal
    event = service.events().insert(calendarId='primary', body=event).execute()
    return event.get('htmlLink')


# Initialiser Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Configurer les clients Google Cloud
credentials = service_account.Credentials.from_service_account_file(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
vision_client = vision.ImageAnnotatorClient(credentials=credentials)
language_client = language_v1.LanguageServiceClient(credentials=credentials)
firestore_client = firestore.Client(credentials=credentials)
storage_client = storage.Client(credentials=credentials)

# Charger le modèle et le vectoriseur au démarrage de l'application
model = joblib.load("models/document_classifier.joblib")
vectorizer = joblib.load("models/tfidf_vectorizer.joblib")

# Nom du bucket Cloud Storage
BUCKET_NAME = os.getenv("BUCKET_NAME")



@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Récupérer le fichier uploadé
        file = request.files["document"]
        if not file:
            flash("Aucun fichier sélectionné.", "error")
            return redirect(url_for("index"))

        # Upload vers Cloud Storage
        blob = storage_client.bucket(BUCKET_NAME).blob(file.filename)
        blob.upload_from_string(file.read(), content_type=file.content_type)

        # Traiter avec Vision API (OCR)
        image = vision.Image()
        image.source.image_uri = f"gs://{BUCKET_NAME}/{file.filename}"
        response = vision_client.text_detection(image=image)
        text = response.full_text_annotation.text if response.full_text_annotation else ""

        # Classifier le texte avec le modèle personnalisé
        text_vectorized = vectorizer.transform([text])
        predicted_label = model.predict(text_vectorized)[0]

        # Classifier avec Natural Language API
        document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
        entities_response = language_client.analyze_entities(document=document)
        entities = [entity.name for entity in entities_response.entities]

        # Extraire la date d'expiration
        expiry_date = extract_expiry_date(text)

        # Si le document est un passeport et qu'une date d'expiration est trouvée
        if predicted_label == "passeport" and expiry_date:
            # Créer un rappel dans Google Calendar
            calendar_event_link = create_calendar_event(expiry_date, predicted_label, file.filename)
            flash(f"Un rappel a été créé dans votre calendrier : {calendar_event_link}", "success")

        # Extraire les dates et métadonnées
        metadata = {"entities": entities, "text": text}

        # Sauvegarder dans Firestore
        doc_ref = firestore_client.collection("documents").document(file.filename)
        doc_ref.set({
            "filename": file.filename,
            "text": text,
            "predicted_label": predicted_label,
            "expiry_date": expiry_date.strftime("%d/%m/%Y") if expiry_date else None,
            "entities": entities,
            "status": "uploaded",
            "created_at": firestore.SERVER_TIMESTAMP
        })

        flash("Document uploadé et traité avec succès ! Type : {predicted_label}", "success")
        return redirect(url_for("index"))

    # Afficher les documents existants
    documents = []
    for doc in firestore_client.collection("documents").stream():
        documents.append(doc.to_dict())

    return render_template("index.html", documents=documents)





if __name__ == "__main__":
    app.run(debug=True)
