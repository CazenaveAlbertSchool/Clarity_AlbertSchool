
## Composants
1. **Frontend** : Flask + Jinja2 (HTML/CSS/JS).
2. **Backend** :
   - Routes Flask (`app.py`).
   - Logique métier (`/utils`).
3. **Stockage** :
   - Fichiers : Google Cloud Storage.
   - Métadonnées : Firestore.
4. **APIs Google** :
   - Vision API : OCR.
   - Natural Language API : NLP.
   - Calendar API : Rappels.

## Décisions Techniques
- **Modularité** : Séparation des responsabilités (ex. : `ocr_utils.py` pour tout ce qui concerne l'OCR).
- **Scalabilité** : Utilisation de services serverless (Cloud Functions possible prévu pour bientôt).
- **Sécurité** : Variables d'environnement pour les clés API, chiffrement des données sensibles.
