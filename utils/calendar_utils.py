from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import timedelta
from config import Config
import logging

logger = logging.getLogger(__name__)

def create_calendar_event(expiry_date, document_type, filename):
    """
    Crée un événement de rappel dans Google Calendar.
    Args:
        expiry_date (datetime): Date d'expiration du document.
        document_type (str): Type de document (ex: "passeport").
        filename (str): Nom du fichier.
    Returns:
        str: Lien vers l'événement créé, ou None en cas d'erreur.
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            Config.GOOGLE_APPLICATION_CREDENTIALS,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        service = build('calendar', 'v3', credentials=credentials)

        reminder_date = expiry_date - timedelta(days=Config.REMINDER_DAYS_BEFORE)
        event = {
            'summary': f"Rappel: Expiration {document_type} ({filename})",
            'description': f"Votre {document_type} expire le {expiry_date.strftime('%d/%m/%Y')}. Pensez à le renouveler!",
            'start': {
                'dateTime': reminder_date.strftime("%Y-%m-%dT09:00:00"),
                'timeZone': Config.CALENDAR_TIMEZONE,
            },
            'end': {
                'dateTime': reminder_date.strftime("%Y-%m-%dT10:00:00"),
                'timeZone': Config.CALENDAR_TIMEZONE,
            },
            'reminders': {
                'useDefault': True,
            },
        }
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        return created_event.get('htmlLink')
    except Exception as e:
        logger.error(f"Erreur lors de la création du rappel: {e}")
        return None
