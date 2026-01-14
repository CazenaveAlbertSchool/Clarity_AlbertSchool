
# Clarity MVP - Système de Gestion Automatique des Factures

Application Flask pour extraire, analyser et gérer automatiquement les factures depuis Google Drive avec notifications par email et rappels dans Google Calendar.

## Fonctionnalités

- 📄 **Extraction automatique** : Télécharge et traite les factures depuis Google Drive
- 🔍 **Classification intelligente** : Identifie automatiquement les factures, devis et avoirs
- 📅 **Extraction de dates** : Extrait automatiquement les dates de paiement avec plusieurs méthodes
- 📧 **Notifications email** : Envoie des rappels automatiques par email
- 📆 **Rappels Calendar** : Crée automatiquement des événements dans Google Calendar
- 💾 **Stockage Firestore** : Sauvegarde toutes les informations extraites

## Structure

- `main.py` : Application Flask principale
- `services/` : Services métier
  - `documentai_service.py` : Traitement des documents avec DocumentAI
  - `drive_service.py` : Gestion Google Drive et filtrage des factures
  - `invoice_service.py` : Classification et extraction de dates de paiement
  - `calendar_service.py` : Création d'événements dans Google Calendar
  - `email_service.py` : Envoi de notifications par email
  - `firestore_service.py` : Sauvegarde dans Firestore
  - `vision_service.py` : OCR avec Vision API
- `templates/` : Interface utilisateur HTML
- `static/` : Fichiers statiques (CSS, JS)

## Prérequis

1. Compte Google Cloud avec les API suivantes activées :
   - Document AI API
   - Vision API
   - Drive API
   - Calendar API
   - Gmail API
   - Firestore API
2. Python 3.8+
3. Credentials Google Cloud configurées (via `gcloud auth application-default login` ou fichier JSON)

## Installation

1. Cloner le projet
2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurer les variables d'environnement (créer un fichier `.env`) :
```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=eu-west1
DOCUMENTAI_PROCESSOR_ID=your-processor-id
SENDER_EMAIL=votre-email@gmail.com
RECIPIENT_EMAIL=destinataire@gmail.com
```

## Variables d'environnement

### Requises
- `GOOGLE_CLOUD_PROJECT` : ID de votre projet Google Cloud
- `GOOGLE_CLOUD_LOCATION` : Localisation (ex: eu-west1)
- `DOCUMENTAI_PROCESSOR_ID` : ID du processeur DocumentAI

### Optionnelles
- `SENDER_EMAIL` : Adresse email de l'expéditeur (pour Gmail API)
- `RECIPIENT_EMAIL` : Adresse email du destinataire (par défaut: SENDER_EMAIL)
- `USE_GCLOUD_AUTH` : Utiliser l'authentification gcloud (true/false)

## Utilisation

1. Démarrer l'application :
```bash
python main.py
```

2. Ouvrir `http://localhost:5000` dans votre navigateur

3. Cliquer sur "Importer depuis Google Drive" pour lister les factures

4. Cliquer sur "Traiter" pour une facture :
   - Extraction automatique du texte
   - Classification du document
   - Extraction de la date de paiement
   - Création automatique d'un rappel Calendar (3 jours avant)
   - Création d'un événement pour le jour de l'échéance
   - Envoi d'un email de rappel

## Déploiement

### Docker
```bash
docker build -t clarity-mvp .
docker run -p 5000:5000 clarity-mvp
```

### Cloud Run
```bash
gcloud run deploy clarity-mvp --source .
```
