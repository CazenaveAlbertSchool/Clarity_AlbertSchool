from flask import Flask, render_template, request, jsonify
import os
from config import GOOGLE_API_KEY, GOOGLE_CLIENT_ID
from services.vision_service import detect_text
from services.documentai_service import process_document
from services.firestore_service import save_result
from services.drive_service import list_files, download_file, list_invoices, list_invoices_in_folder
from services.invoice_service import process_invoice
from services.calendar_service import create_payment_reminder, create_payment_event
from services.email_service import send_payment_reminder_email

app = Flask(__name__)
# os.makedirs("temp", exist_ok=True)
# Crée le dossier temp/ avec un chemin absolu
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Route pour la page d'accueil (unique)
@app.route('/')
def home():
    return render_template(
        'index.html',
        google_api_key=GOOGLE_API_KEY,
        google_client_id=GOOGLE_CLIENT_ID,
    )

# Route pour traiter les fichiers uploadés
@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        app.logger.error("Aucun fichier dans la requête.")
        return jsonify({"error": "Aucun fichier sélectionné"}), 400

    file = request.files['file']
    if file.filename == '':
        app.logger.error("Fichier vide.")
        return jsonify({"error": "Fichier vide"}), 400

    if file:
        # Utilise un chemin absolu pour sauvegarder et traiter le fichier
        file_path = os.path.join(TEMP_DIR, file.filename)
        abs_path = os.path.abspath(file_path)
        app.logger.info(f"Sauvegarde du fichier : {abs_path}")
        file.save(abs_path)

        # Vérifie que le fichier existe après sauvegarde
        if not os.path.exists(abs_path):
            app.logger.error(f"Fichier introuvable après sauvegarde : {abs_path}")
            return jsonify({"error": "Fichier introuvable après sauvegarde"}), 500

        # Passe le chemin absolu à detect_text
        text = detect_text(abs_path)
        if text is None:
            app.logger.error("Échec de la détection de texte.")
            return jsonify({"error": "Échec de la détection de texte"}), 500

        return jsonify({"status": "success", "text": text})


# Route pour lister les fichiers Google Drive
@app.route('/list-drive-files')
def list_drive_files():
    """Liste tous les fichiers (optionnel: filtrer par type MIME)."""
    mime_type = request.args.get('mime_type', None)
    invoice_only = request.args.get('invoice_only', 'false').lower() == 'true'
    
    if invoice_only:
        files = list_invoices()
    else:
        files = list_files(mime_type=mime_type)
    
    return jsonify({"files": files})

# Route pour lister uniquement les factures
@app.route('/list-invoices')
def list_invoices_route():
    """Liste uniquement les factures dans Google Drive."""
    files = list_invoices()
    return jsonify({"files": files, "count": len(files)})

# Route pour traiter un fichier Google Drive
@app.route('/process-drive-file', methods=['POST'])
def process_drive_file():
    data = request.json
    file_id = data.get('file_id')
    file_name = data.get('file_name')
    create_notifications = data.get('create_notifications', True)  # Par défaut, créer les notifications

    if not file_id or not file_name:
        return jsonify({"error": "file_id et file_name sont requis"}), 400

    result = process_drive_file_core(file_id, file_name, create_notifications)
    return jsonify(result)


def process_drive_file_core(file_id, file_name, create_notifications=True):
    """
    Coeur de traitement pour un fichier Google Drive:
    téléchargement, DocumentAI, classification, Firestore, notifications.

    Args:
        file_id: ID du fichier dans Drive
        file_name: Nom du fichier
        create_notifications: Active ou non la création de notifications

    Returns:
        dict: Résultat complet du traitement
    """
    file_path = download_file(file_id, file_name)
    if not file_path:
        return {"error": "Échec du téléchargement depuis Google Drive"}

    # Traite directement avec DocumentAI (qui fait OCR + extraction d'entités)
    documentai_result = process_document(file_path)
    if documentai_result is None:
        return {"error": "Échec du traitement Document AI"}

    # Utilise le texte extrait par DocumentAI
    text = documentai_result.get("full_text", "")
    entities = documentai_result.get("entities", [])

    # Optionnel: utilise aussi Vision API pour comparaison/fallback
    if not text:
        text = detect_text(file_path)
        if text is None:
            return {"error": "Échec de la détection de texte"}

    # Classifie le document et extrait la date de paiement
    invoice_info = process_invoice(text, entities)
    classification = invoice_info.get("classification", {})
    payment_info = invoice_info.get("payment_date", {})

    # Vérifie si c'est bien une facture
    if not classification.get("is_invoice", False):
        app.logger.warning(
            f"Le document {file_name} ne semble pas être une facture "
            f"(confiance: {classification.get('confidence', 0):.2f})"
        )

    # Sauvegarde dans Firestore avec les informations supplémentaires
    doc_id = save_result(file_name, text, documentai_result, classification, payment_info)

    # Initialise les résultats des notifications
    calendar_result = None
    email_result = None

    # Crée les notifications si c'est une facture avec une date de paiement et si activé
    if create_notifications and classification.get("is_invoice", False) and payment_info.get("payment_date"):
        payment_date = payment_info.get("payment_date")

        # Extrait des informations supplémentaires pour les notifications
        invoice_data = {
            "name": file_name,
            "amount": None,
            "vendor": None,
            "invoice_number": None
        }

        # Essaie d'extraire le montant et le fournisseur depuis les entités
        for entity in entities:
            entity_type = entity.get("type", "").lower()
            if "amount" in entity_type or "total" in entity_type:
                invoice_data["amount"] = entity.get("text")
            elif "vendor" in entity_type or "organization" in entity_type:
                invoice_data["vendor"] = entity.get("text")
            elif "invoice_id" in entity_type or "invoice_number" in entity_type:
                invoice_data["invoice_number"] = entity.get("text")

        # Crée un rappel dans Calendar (3 jours avant)
        try:
            calendar_result = create_payment_reminder(
                invoice_name=file_name,
                payment_date=payment_date,
                invoice_info=invoice_data
            )
            if calendar_result.get("success"):
                app.logger.info(f"Rappel Calendar créé: {calendar_result.get('event_link')}")
            else:
                app.logger.warning(f"Échec création rappel Calendar: {calendar_result.get('error')}")
        except Exception as e:
            app.logger.error(f"Erreur lors de la création du rappel Calendar: {e}")

        # Crée un événement pour le jour de l'échéance
        try:
            event_result = create_payment_event(
                invoice_name=file_name,
                payment_date=payment_date,
                invoice_info=invoice_data
            )
            if event_result.get("success"):
                app.logger.info(f"Événement échéance créé: {event_result.get('event_link')}")
        except Exception as e:
            app.logger.error(f"Erreur lors de la création de l'événement: {e}")

        # Envoie un email de rappel
        try:
            email_result = send_payment_reminder_email(
                invoice_name=file_name,
                payment_date=payment_date,
                invoice_info=invoice_data
            )
            if email_result.get("success"):
                app.logger.info(f"Email de rappel envoyé: {email_result.get('message_id')}")
            else:
                app.logger.warning(f"Échec envoi email: {email_result.get('error')}")
        except Exception as e:
            app.logger.error(f"Erreur lors de l'envoi de l'email: {e}")

    return {
        "status": "success",
        "document_id": doc_id,
        "file_name": file_name,
        "text": text,
        "entities": entities,
        "classification": {
            "is_invoice": classification.get("is_invoice", False),
            "confidence": classification.get("confidence", 0.0),
            "invoice_type": classification.get("invoice_type", "unknown"),
            "indicators": classification.get("indicators", [])
        },
        "payment_date": {
            "date": payment_info.get("date_string"),
            "datetime": payment_info.get("payment_date").isoformat() if payment_info.get("payment_date") else None,
            "confidence": payment_info.get("confidence", 0.0),
            "method": payment_info.get("method")
        },
        "notifications": {
            "calendar": calendar_result,
            "email": email_result
        }
    }


@app.route('/process-drive-folder', methods=['POST'])
def process_drive_folder():
    """
    Traite automatiquement tous les fichiers d'un dossier Drive (par défaut 'Factures').

    Body JSON possible:
        - folder_name: nom du dossier (par défaut 'Factures')
        - create_notifications: bool (par défaut True)
    """
    data = request.json or {}
    folder_name = data.get('folder_name', 'Factures')
    create_notifications = data.get('create_notifications', True)

    # Liste les factures dans le dossier
    files = list_invoices_in_folder(folder_name)
    if not files:
        return jsonify({
            "status": "no_files",
            "folder_name": folder_name,
            "message": f"Aucune facture trouvée dans le dossier '{folder_name}'"
        })

    results = []
    for f in files:
        file_id = f.get('id')
        file_name = f.get('name')
        if not file_id or not file_name:
            continue
        res = process_drive_file_core(file_id, file_name, create_notifications)
        results.append(res)

    return jsonify({
        "status": "success",
        "folder_name": folder_name,
        "file_count": len(files),
        "results": results
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
