# Clarity MVP

**Description** : Outil d'organisation de documents administratifs avec rappels automatiques via Google Calendar.

## Fonctionnalités
- Upload et OCR de documents (PDF, images).
- Classification automatique (passeport, facture, etc.).
- Rappels d'expiration via Google Calendar.
- Interface web simple.

## Prérequis
- Compte Google Cloud avec les APIs activées :
  - Vision API
  - Natural Language API
  - Calendar API
  - Firestore
  - Cloud Storage
- Python 3.9+
- Clé de service Google Cloud (JSON).

## Installation
1. Cloner le dépôt :
   ```bash
   git clone https://github.com/ton-utilisateur/clarity_mvp.git
   cd clarity_mvp
2. Créer un environnement virtuel :
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\activate     # Windows

3. Installer les dépendances :

    ```bash
    pip install -r requirements.txt

4. Configurer .env (copier .env.example et compléter).

5. Lancer l'application :

    ```bash
    flask run

## Déploiement
1. Local : 
    ```bash
    flask run
    Accès : http://localhost:5000

2. Docker :
    ```Bash
    Construction de l'image
    docker build -t clarity .

## Lancement du conteneur
docker run -p 5000:5000 clarity
### Google App Engine (Cloud)
Pour déployer en production sur Google Cloud Platform :
    ```Bash
    gcloud app deploy

## 📂 Structure du Projet
L'architecture suit les standards d'une application Flask modulaire :

Plaintext

clarity_mvp/
├── app.py              # Point d'entrée principal de l'application Flask
├── config.py           # Paramètres et variables d'environnement
├── /models             # Modèles de Machine Learning entraînés (ex: .pkl, .h5)
├── /static             # Fichiers statiques (CSS, JavaScript, Images)
├── /templates          # Fichiers HTML (Jinja2)
└── /utils              # Fonctions utilitaires et logique métier


## Contribuer

Fork le projet.
Crée une branche (git checkout -b feature/ma-fonctionnalite).
Commit tes changements (git commit -am 'Ajout de X').
Push (git push origin feature/ma-fonctionnalite).
Ouvre une Pull Request.
Copier






