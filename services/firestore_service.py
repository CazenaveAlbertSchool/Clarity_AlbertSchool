from google.cloud import firestore
from google.auth import default
from google.api_core.exceptions import GoogleAPICallError
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_result(file_name, text, document_data, classification=None, payment_date=None):
    """
    Sauvegarde les résultats du traitement dans Firestore.
    
    Args:
        file_name: Nom du fichier
        text: Texte extrait
        document_data: Données extraites par DocumentAI
        classification: Dict avec les informations de classification (optionnel)
        payment_date: Dict avec les informations de date de paiement (optionnel)
    
    Returns:
        str: ID du document créé, ou None en cas d'erreur
    """
    try:
        credentials, _ = default()
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')

        if not project_id:
            logger.error("GOOGLE_CLOUD_PROJECT non configuré.")
            return None
        db = firestore.Client(credentials=credentials, project=project_id)

        doc_data = {
            'file_name': file_name,
            'text': text[:10000],  # Limite la taille du texte stocké
            'entities': document_data.get('entities', []),
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        
        # Ajoute les informations de classification si disponibles
        if classification:
            doc_data['classification'] = {
                'is_invoice': classification.get('is_invoice', False),
                'confidence': classification.get('confidence', 0.0),
                'invoice_type': classification.get('invoice_type', 'unknown'),
                'indicators': classification.get('indicators', [])
            }
        
        # Ajoute les informations de date de paiement si disponibles
        if payment_date and payment_date.get('payment_date'):
            payment_dt = payment_date.get('payment_date')
            doc_data['payment_date'] = {
                'date_string': payment_date.get('date_string'),
                'datetime': payment_dt.isoformat() if payment_dt else None,
                'timestamp': payment_dt if payment_dt else None,  # Pour les requêtes de date
                'confidence': payment_date.get('confidence', 0.0),
                'method': payment_date.get('method')
            }

        doc_ref = db.collection('documents').document()
        doc_ref.set(doc_data)
        
        logger.info(f"Document sauvegardé dans Firestore avec ID: {doc_ref.id}")
        return doc_ref.id

    except GoogleAPICallError as e:
        logger.error(f"Erreur Firestore: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}", exc_info=True)
        return None
