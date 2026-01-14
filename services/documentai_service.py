from google.cloud import documentai_v1 as documentai
from google.auth import default
from google.api_core.exceptions import GoogleAPICallError
from dotenv import load_dotenv
import os
import logging
import mimetypes

load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_mime_type(file_path):
    """Détermine le type MIME d'un fichier à partir de son extension."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        # Types MIME par défaut pour les extensions communes
        ext = os.path.splitext(file_path)[1].lower()
        mime_map = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.tiff': 'image/tiff',
            '.bmp': 'image/bmp'
        }
        mime_type = mime_map.get(ext, 'application/pdf')
    return mime_type

def process_document(file_path):
    """
    Traite un document (PDF, image) avec DocumentAI.
    
    Args:
        file_path: Chemin vers le fichier à traiter (PDF ou image)
    
    Returns:
        dict avec 'entities' et 'full_text', ou None en cas d'erreur
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"Fichier introuvable: {file_path}")
            return None

        credentials, _ = default()
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('GOOGLE_CLOUD_LOCATION')
        processor_id = os.getenv('DOCUMENTAI_PROCESSOR_ID')

        if not project_id or not location or not processor_id:
            logger.error("Variables d'environnement manquantes: GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION ou DOCUMENTAI_PROCESSOR_ID.")
            return None

        processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
        client = documentai.DocumentProcessorServiceClient(credentials=credentials)

        # Lit le contenu binaire du fichier
        with open(file_path, 'rb') as f:
            file_content = f.read()

        # Détermine le type MIME
        mime_type = get_mime_type(file_path)
        logger.info(f"Traitement du fichier {file_path} avec type MIME: {mime_type}")

        # Crée la requête avec le document binaire
        raw_document = documentai.RawDocument(
            content=file_content,
            mime_type=mime_type
        )
        
        request = documentai.ProcessRequest(
            name=processor_name,
            raw_document=raw_document
        )
        
        result = client.process_document(request=request)

        # Extrait les entités
        entities = []
        if result.document.entities:
            for entity in result.document.entities:
                entities.append({
                    "type": entity.type_,
                    "text": entity.mention_text,
                    "confidence": getattr(entity, 'confidence', None)
                })

        return {
            "entities": entities,
            "full_text": result.document.text
        }

    except GoogleAPICallError as e:
        logger.error(f"Erreur Document AI: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors du traitement DocumentAI: {e}", exc_info=True)
        return None
