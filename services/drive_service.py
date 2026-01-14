from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from google.auth import default
from dotenv import load_dotenv
import io
import os
import logging
import re

load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_drive_service():
    credentials, _ = default()
    return build('drive', 'v3', credentials=credentials)

def is_invoice_file(file_name):
    """
    Détermine si un fichier est probablement une facture basé sur son nom.
    
    Args:
        file_name: Nom du fichier
    
    Returns:
        bool: True si le fichier semble être une facture
    """
    if not file_name:
        return False
    
    file_name_lower = file_name.lower()
    
    # Mots-clés français et anglais pour identifier les factures
    invoice_keywords = [
        'facture', 'invoice', 'bill', 'note', 'note de', 
        'avoir', 'credit note', 'devis', 'quote', 'quotation',
        'recu', 'receipt', 'bon de', 'bon de commande'
    ]
    
    # Extensions de fichiers acceptées pour les factures
    invoice_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.gif']
    
    # Vérifie l'extension
    has_valid_extension = any(file_name_lower.endswith(ext) for ext in invoice_extensions)
    
    # Vérifie les mots-clés dans le nom
    has_invoice_keyword = any(keyword in file_name_lower for keyword in invoice_keywords)
    
    # Vérifie les patterns communs (ex: FACTURE_2024, Invoice-123, etc.)
    has_invoice_pattern = bool(re.search(r'(facture|invoice|bill)[\s_-]?\d+', file_name_lower))
    
    return has_valid_extension and (has_invoice_keyword or has_invoice_pattern)

def list_files(mime_type=None, invoice_only=False):
    """
    Liste les fichiers dans Google Drive.
    
    Args:
        mime_type: Type MIME à filtrer (ex: 'application/pdf', 'image/jpeg')
        invoice_only: Si True, filtre uniquement les fichiers qui semblent être des factures
    
    Returns:
        list: Liste de dictionnaires avec 'id' et 'name'
    """
    try:
        service = get_drive_service()
        
        # Construit la requête de base
        query_parts = []
        
        # Filtre par type MIME si spécifié
        if mime_type:
            query_parts.append(f"mimeType='{mime_type}'")
        
        # Filtre pour exclure les dossiers et fichiers Google (Docs, Sheets, etc.)
        query_parts.append("mimeType!='application/vnd.google-apps.folder'")
        query_parts.append("trashed=false")
        
        # Combine les conditions
        query = " and ".join(query_parts) if query_parts else None
        
        # Types MIME acceptés pour les factures (PDF et images)
        invoice_mime_types = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/tiff',
            'image/gif',
            'image/bmp'
        ]
        
        # Si on cherche des factures, on filtre aussi par type MIME
        if invoice_only and not mime_type:
            mime_query = " or ".join([f"mimeType='{mime}'" for mime in invoice_mime_types])
            if query:
                query = f"({query}) and ({mime_query})"
            else:
                query = mime_query
        
        logger.info(f"Requête Drive: {query}")
        results = service.files().list(
            q=query, 
            pageSize=100,  # Augmenté pour avoir plus de résultats
            fields="files(id, name, mimeType, modifiedTime)"
        ).execute()
        
        files = results.get('files', [])
        
        # Filtre par nom si invoice_only est True
        if invoice_only:
            files = [f for f in files if is_invoice_file(f.get('name', ''))]
            logger.info(f"Fichiers filtrés (factures uniquement): {len(files)}")
        
        return files

    except HttpError as e:
        logger.error(f"Erreur Drive API: {e}")
        return []
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la liste des fichiers: {e}", exc_info=True)
        return []

def list_invoices():
    """
    Liste uniquement les factures dans Google Drive.
    Utilise un filtre intelligent pour identifier les factures.
    
    Returns:
        list: Liste de factures avec 'id', 'name', 'mimeType', 'modifiedTime'
    """
    return list_files(invoice_only=True)

def download_file(file_id, file_name):
    """
    Télécharge un fichier depuis Google Drive.
    
    Args:
        file_id: ID du fichier dans Google Drive
        file_name: Nom du fichier à sauvegarder
    
    Returns:
        str: Chemin absolu du fichier téléchargé, ou None en cas d'erreur
    """
    try:
        # Utilise un chemin absolu pour la cohérence avec main.py
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        TEMP_DIR = os.path.join(BASE_DIR, "temp")
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        service = get_drive_service()
        request = service.files().get_media(fileId=file_id)
        
        file_path = os.path.join(TEMP_DIR, file_name)
        abs_path = os.path.abspath(file_path)
        
        logger.info(f"Téléchargement du fichier {file_name} vers {abs_path}")

        with io.FileIO(abs_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Progression: {int(status.progress() * 100)}%")

        logger.info(f"Fichier téléchargé avec succès: {abs_path}")
        return abs_path

    except HttpError as e:
        logger.error(f"Erreur Drive API lors du téléchargement: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors du téléchargement: {e}", exc_info=True)
        return None
