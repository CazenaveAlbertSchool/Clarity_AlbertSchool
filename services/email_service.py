"""
Service pour envoyer des notifications par email.
Utilise Gmail API ou SMTP selon la configuration.
"""
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth import default
from dotenv import load_dotenv
from datetime import datetime
from dateutil import parser as date_parser

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_gmail_service():
    """
    Initialise et retourne le service Gmail.
    
    Returns:
        googleapiclient.discovery.Resource: Service Gmail ou None
    """
    try:
        credentials, _ = default()
        service = build('gmail', 'v1', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du service Gmail: {e}")
        return None

def get_sender_email():
    """
    Récupère l'adresse email de l'expéditeur depuis les variables d'environnement.
    
    Returns:
        str: Adresse email ou None
    """
    sender_email = os.getenv('SENDER_EMAIL')
    if not sender_email:
        # Essaie de récupérer depuis les credentials Google
        try:
            credentials, _ = default()
            if hasattr(credentials, 'service_account_email'):
                return credentials.service_account_email
        except:
            pass
    return sender_email

def send_payment_reminder_email(invoice_name, payment_date, recipient_email=None, invoice_info=None):
    """
    Envoie un email de rappel pour une date de paiement.
    
    Args:
        invoice_name: Nom de la facture
        payment_date: Date de paiement (datetime ou string ISO)
        recipient_email: Adresse email du destinataire (si None, utilise SENDER_EMAIL)
        invoice_info: Dict avec informations supplémentaires (optionnel)
    
    Returns:
        dict avec 'success', 'message_id', ou erreur
    """
    try:
        # Convertit la date en datetime si nécessaire
        if isinstance(payment_date, str):
            payment_dt = date_parser.parse(payment_date)
        else:
            payment_dt = payment_date
        
        if not payment_dt:
            return {"success": False, "error": "Date de paiement invalide"}
        
        # Détermine le destinataire
        if not recipient_email:
            recipient_email = os.getenv('RECIPIENT_EMAIL')
            if not recipient_email:
                recipient_email = get_sender_email()
        
        if not recipient_email:
            return {"success": False, "error": "Aucune adresse email de destinataire configurée"}
        
        sender_email = get_sender_email()
        if not sender_email:
            return {"success": False, "error": "Aucune adresse email d'expéditeur configurée"}
        
        # Calcule les jours restants
        days_until = (payment_dt.date() - datetime.now().date()).days
        
        # Sujet de l'email
        if days_until < 0:
            subject = f"⚠️ Échéance dépassée - Paiement facture: {invoice_name}"
        elif days_until == 0:
            subject = f"🔴 Échéance aujourd'hui - Paiement facture: {invoice_name}"
        elif days_until <= 3:
            subject = f"🟠 Rappel urgent - Paiement facture: {invoice_name} (dans {days_until} jour(s))"
        else:
            subject = f"📅 Rappel - Paiement facture: {invoice_name} (dans {days_until} jour(s))"
        
        # Corps de l'email en HTML
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Rappel de paiement</h2>
                
                <p>Bonjour,</p>
                
                <p>Ceci est un rappel automatique concernant le paiement de la facture suivante :</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0;">
                    <p><strong>Facture :</strong> {invoice_name}</p>
                    <p><strong>Date d'échéance :</strong> {payment_dt.strftime('%d/%m/%Y')}</p>
                    <p><strong>Jours restants :</strong> {days_until} jour(s)</p>
        """
        
        if invoice_info:
            if invoice_info.get('amount'):
                html_body += f'<p><strong>Montant :</strong> {invoice_info.get("amount")}</p>'
            if invoice_info.get('vendor'):
                html_body += f'<p><strong>Fournisseur :</strong> {invoice_info.get("vendor")}</p>'
            if invoice_info.get('invoice_number'):
                html_body += f'<p><strong>Numéro de facture :</strong> {invoice_info.get("invoice_number")}</p>'
        
        html_body += """
                </div>
                
                <p style="color: #e74c3c; font-weight: bold;">
                    Veuillez procéder au paiement avant la date d'échéance.
                </p>
                
                <p>Cordialement,<br>Clarity - Système de gestion des factures</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #7f8c8d;">
                    Ce message a été généré automatiquement. Merci de ne pas répondre à cet email.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Version texte simple
        text_body = f"""
Rappel de paiement

Bonjour,

Ceci est un rappel automatique concernant le paiement de la facture suivante :

Facture : {invoice_name}
Date d'échéance : {payment_dt.strftime('%d/%m/%Y')}
Jours restants : {days_until} jour(s)
"""
        
        if invoice_info:
            if invoice_info.get('amount'):
                text_body += f"Montant : {invoice_info.get('amount')}\n"
            if invoice_info.get('vendor'):
                text_body += f"Fournisseur : {invoice_info.get('vendor')}\n"
        
        text_body += "\nVeuillez procéder au paiement avant la date d'échéance.\n\nCordialement,\nClarity - Système de gestion des factures"
        
        # Utilise Gmail API pour envoyer l'email
        return send_email_gmail(sender_email, recipient_email, subject, html_body, text_body)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email: {e}", exc_info=True)
        return {"success": False, "error": f"Erreur inattendue: {str(e)}"}

def send_email_gmail(sender_email, recipient_email, subject, html_body, text_body):
    """
    Envoie un email via Gmail API.
    
    Args:
        sender_email: Adresse email de l'expéditeur
        recipient_email: Adresse email du destinataire
        subject: Sujet de l'email
        html_body: Corps HTML de l'email
        text_body: Corps texte de l'email
    
    Returns:
        dict avec 'success', 'message_id', ou erreur
    """
    try:
        service = get_gmail_service()
        if not service:
            return {"success": False, "error": "Impossible d'initialiser le service Gmail"}
        
        # Crée le message
        message = MIMEMultipart('alternative')
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = subject
        
        # Ajoute les parties texte et HTML
        part1 = MIMEText(text_body, 'plain', 'utf-8')
        part2 = MIMEText(html_body, 'html', 'utf-8')
        
        message.attach(part1)
        message.attach(part2)
        
        # Encode le message en base64
        import base64
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Envoie le message
        send_message = {'raw': raw_message}
        sent_message = service.users().messages().send(userId='me', body=send_message).execute()
        
        message_id = sent_message.get('id')
        logger.info(f"Email envoyé avec succès. Message ID: {message_id}")
        
        return {
            "success": True,
            "message_id": message_id,
            "recipient": recipient_email
        }
        
    except HttpError as e:
        logger.error(f"Erreur Gmail API: {e}")
        return {"success": False, "error": f"Erreur Gmail API: {str(e)}"}
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'envoi de l'email: {e}", exc_info=True)
        return {"success": False, "error": f"Erreur inattendue: {str(e)}"}

def send_notification_summary(invoices_data):
    """
    Envoie un résumé des factures à payer.
    
    Args:
        invoices_data: Liste de dicts avec les informations des factures
    
    Returns:
        dict avec 'success', 'message_id', ou erreur
    """
    try:
        recipient_email = os.getenv('RECIPIENT_EMAIL') or get_sender_email()
        sender_email = get_sender_email()
        
        if not recipient_email or not sender_email:
            return {"success": False, "error": "Adresses email non configurées"}
        
        # Construit le résumé
        subject = f"📊 Résumé des factures - {len(invoices_data)} facture(s) à traiter"
        
        html_body = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Résumé des factures</h2>
                <p>Voici un résumé des factures à traiter :</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <thead>
                        <tr style="background-color: #3498db; color: white;">
                            <th style="padding: 10px; text-align: left;">Facture</th>
                            <th style="padding: 10px; text-align: left;">Date d'échéance</th>
                            <th style="padding: 10px; text-align: left;">Jours restants</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for invoice in invoices_data:
            payment_date = invoice.get('payment_date')
            if isinstance(payment_date, str):
                payment_dt = date_parser.parse(payment_date)
            else:
                payment_dt = payment_date
            
            days_until = (payment_dt.date() - datetime.now().date()).days if payment_dt else 0
            
            color = "#e74c3c" if days_until < 0 else "#f39c12" if days_until <= 3 else "#27ae60"
            
            html_body += f"""
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 10px;">{invoice.get('name', 'N/A')}</td>
                            <td style="padding: 10px;">{payment_dt.strftime('%d/%m/%Y') if payment_dt else 'N/A'}</td>
                            <td style="padding: 10px; color: {color}; font-weight: bold;">{days_until} jour(s)</td>
                        </tr>
            """
        
        html_body += """
                    </tbody>
                </table>
                <p>Cordialement,<br>Clarity - Système de gestion des factures</p>
            </div>
        </body>
        </html>
        """
        
        return send_email_gmail(sender_email, recipient_email, subject, html_body, "")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du résumé: {e}", exc_info=True)
        return {"success": False, "error": f"Erreur: {str(e)}"}
