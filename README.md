
# Projet de Traitement de Documents avec Google Cloud

Ce projet permet de traiter des documents stockés dans Google Drive en utilisant Vision API pour l'OCR, Document AI pour la classification, et Firestore pour le stockage.

## Structure
- `app/` : Code source Flask
- `app/services/` : Logique métier pour chaque API Google
- `app/templates/` : Interface utilisateur
- `app/static/` : Fichiers statiques

## Prérequis
1. Compte Google Cloud avec les API activées
3. Docker pour le déploiement sur Cloud Run

## Déploiement
1. Construire l'image Docker : `docker build -t documents-app .`
2. Déployer sur Cloud Run : `gcloud run deploy --source .`

## Variables d'environnement
- `GOOGLE_APPLICATION_CREDENTIALS` : Chemin vers le fichier de clé
- `GOOGLE_CLOUD_PROJECT` : ID de ton projet Google Cloud
- `DOCUMENTAI_PROCESSOR_ID` : ID du processeur Document AI
