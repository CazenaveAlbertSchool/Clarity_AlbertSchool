"""
Service pour créer des événements et rappels dans Google Calendar.
"""
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth import default
from dotenv import load_dotenv
import os
import logging
from datetime import datetime, timedelta
from dateutil import parser as date_parser

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_calendar_service():
    """
    Initialise et retourne le service Google Calendar.
    
    Returns:
        googleapiclient.discovery.Resource: Service Calendar
    """
    try:
        credentials, _ = default()
        service = build('calendar', 'v3', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du service Calendar: {e}")
        return None

def create_payment_reminder(invoice_name, payment_date, invoice_info=None, calendar_id='primary'):
    """
    Crée un événement de rappel pour une date de paiement dans Google Calendar.
    
    Args:
        invoice_name: Nom de la facture
        payment_date: Date de paiement (datetime ou string ISO)
        invoice_info: Dict avec informations supplémentaires (optionnel)
        calendar_id: ID du calendrier (par défaut 'primary')
    
    Returns:
        dict avec 'success', 'event_id', 'event_link', ou None en cas d'erreur
    """
    try:
        service = get_calendar_service()
        if not service:
            return {"success": False, "error": "Impossible d'initialiser le service Calendar"}
        
        # Convertit la date en datetime si nécessaire
        if isinstance(payment_date, str):
            payment_dt = date_parser.parse(payment_date)
        else:
            payment_dt = payment_date
        
        if not payment_dt:
            return {"success": False, "error": "Date de paiement invalide"}
        
        # Crée un rappel 3 jours avant la date de paiement
        reminder_date = payment_dt - timedelta(days=3)
        
        # Si la date de rappel est dans le passé, utilise la date de paiement elle-même
        if reminder_date < datetime.now():
            reminder_date = payment_dt
        
        # Titre de l'événement
        title = f"💳 Paiement facture: {invoice_name}"
        
        # Description de l'événement
        description_parts = [
            f"Rappel de paiement pour la facture: {invoice_name}",
            f"Date de paiement: {payment_dt.strftime('%d/%m/%Y')}"
        ]
        
        if invoice_info:
            if invoice_info.get('amount'):
                description_parts.append(f"Montant: {invoice_info.get('amount')}")
            if invoice_info.get('vendor'):
                description_parts.append(f"Fournisseur: {invoice_info.get('vendor')}")
            if invoice_info.get('invoice_number'):
                description_parts.append(f"Numéro: {invoice_info.get('invoice_number')}")
        
        description = "\n".join(description_parts)
        
        # Crée l'événement
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': reminder_date.isoformat(),
                'timeZone': 'Europe/Paris',
            },
            'end': {
                'dateTime': (reminder_date + timedelta(hours=1)).isoformat(),
                'timeZone': 'Europe/Paris',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # Email 1 jour avant
                    {'method': 'popup', 'minutes': 15},  # Notification 15 min avant
                ],
            },
            'colorId': '11',  # Rouge pour les rappels importants
        }
        
        # Insère l'événement dans le calendrier
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        
        logger.info(f"Événement créé dans Calendar: {event.get('htmlLink')}")
        
        return {
            "success": True,
            "event_id": event.get('id'),
            "event_link": event.get('htmlLink'),
            "reminder_date": reminder_date.isoformat(),
            "payment_date": payment_dt.isoformat()
        }
        
    except HttpError as e:
        logger.error(f"Erreur Calendar API: {e}")
        return {"success": False, "error": f"Erreur Calendar API: {str(e)}"}
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la création de l'événement: {e}", exc_info=True)
        return {"success": False, "error": f"Erreur inattendue: {str(e)}"}

def create_payment_event(invoice_name, payment_date, invoice_info=None, calendar_id='primary'):
    """
    Crée un événement pour le jour même de la date de paiement.
    
    Args:
        invoice_name: Nom de la facture
        payment_date: Date de paiement (datetime ou string ISO)
        invoice_info: Dict avec informations supplémentaires (optionnel)
        calendar_id: ID du calendrier (par défaut 'primary')
    
    Returns:
        dict avec 'success', 'event_id', 'event_link', ou None en cas d'erreur
    """
    try:
        service = get_calendar_service()
        if not service:
            return {"success": False, "error": "Impossible d'initialiser le service Calendar"}
        
        # Convertit la date en datetime si nécessaire
        if isinstance(payment_date, str):
            payment_dt = date_parser.parse(payment_date)
        else:
            payment_dt = payment_date
        
        if not payment_dt:
            return {"success": False, "error": "Date de paiement invalide"}
        
        # Titre de l'événement
        title = f"📅 Échéance paiement: {invoice_name}"
        
        # Description
        description_parts = [
            f"Date d'échéance pour la facture: {invoice_name}",
            f"Date de paiement: {payment_dt.strftime('%d/%m/%Y')}"
        ]
        
        if invoice_info:
            if invoice_info.get('amount'):
                description_parts.append(f"Montant: {invoice_info.get('amount')}")
            if invoice_info.get('vendor'):
                description_parts.append(f"Fournisseur: {invoice_info.get('vendor')}")
        
        description = "\n".join(description_parts)
        
        # Crée l'événement pour toute la journée
        event = {
            'summary': title,
            'description': description,
            'start': {
                'date': payment_dt.strftime('%Y-%m-%d'),
                'timeZone': 'Europe/Paris',
            },
            'end': {
                'date': payment_dt.strftime('%Y-%m-%d'),
                'timeZone': 'Europe/Paris',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # Email 1 jour avant
                    {'method': 'popup', 'minutes': 0},  # Notification le jour même
                ],
            },
            'colorId': '6',  # Orange pour les échéances
        }
        
        # Insère l'événement
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        
        logger.info(f"Événement d'échéance créé dans Calendar: {event.get('htmlLink')}")
        
        return {
            "success": True,
            "event_id": event.get('id'),
            "event_link": event.get('htmlLink'),
            "payment_date": payment_dt.isoformat()
        }
        
    except HttpError as e:
        logger.error(f"Erreur Calendar API: {e}")
        return {"success": False, "error": f"Erreur Calendar API: {str(e)}"}
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la création de l'événement: {e}", exc_info=True)
        return {"success": False, "error": f"Erreur inattendue: {str(e)}"}

def list_calendars():
    """
    Liste tous les calendriers disponibles.
    
    Returns:
        list: Liste de calendriers avec 'id' et 'summary'
    """
    try:
        service = get_calendar_service()
        if not service:
            return []
        
        calendars = service.calendarList().list().execute()
        return calendars.get('items', [])
        
    except HttpError as e:
        logger.error(f"Erreur lors de la liste des calendriers: {e}")
        return []
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}", exc_info=True)
        return []
