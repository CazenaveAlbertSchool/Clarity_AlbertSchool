import os
import joblib
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from config import Config

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_sample_data():
    """
    Charge des données d'entraînement d'exemple.
    À remplacer par tes propres données (ex. : depuis un CSV ou une base de données).
    Format attendu : liste de dictionnaires {"text": str, "label": str}.
    """
    # Exemple de données (à étendre avec tes propres échantillons)
    documents = [
        {"text": "République Française Carte Nationale d'Identité Valable jusqu'au 15/05/2025", "label": "cni"},
        {"text": "Passeport Français Valable jusqu'au 30/11/2026", "label": "passeport"},
        {"text": "Facture Électricité EDF N°12345 Date: 01/10/2023", "label": "facture"},
        {"text": "Certificat de Scolarité 2023-2024 École Primaire", "label": "certificat_scolaire"},
        {"text": "Contrat de travail CDI Société XYZ", "label": "contrat"},
        {"text": "Assurance Habitation Police N°ABC123", "label": "assurance"},
        {"text": "Permis de conduire Catégorie B Valable jusqu'au 20/03/2027", "label": "permis"},
        {"text": "Quittance de loyer Mois de septembre 2023", "label": "quittance"},
        {"text": "Relevé de compte bancaire IBAN FR761234567890", "label": "releve_bancaire"},
    ]
    return documents

def train_and_save_model():
    """
    Entraîne un modèle de classification et sauvegarde le modèle + vectoriseur.
    """
    try:
        # 1. Charger les données
        documents = load_sample_data()
        if not documents:
            raise ValueError("Aucune donnée d'entraînement disponible.")

        X = [doc["text"] for doc in documents]
        y = [doc["label"] for doc in documents]

        logger.info(f"Entraînement du modèle avec {len(documents)} échantillons.")

        # 2. Vectorisation du texte (TF-IDF)
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='french',  # Ignore les mots courants en français
            ngram_range=(1, 2),   # Considère les unigrams et bigrams
            min_df=1              # Ignore les termes trop rares
        )
        X_vectorized = vectorizer.fit_transform(X)

        # 3. Entraînement du modèle (Random Forest)
        model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight='balanced'  # Équilibre les classes si déséquilibrées
        )
        model.fit(X_vectorized, y)

        # 4. Évaluation (optionnelle)
        X_train, X_test, y_train, y_test = train_test_split(
            X_vectorized, y, test_size=0.2, random_state=42
        )
        y_pred = model.predict(X_test)
        logger.info("Rapport de classification:\n" + classification_report(y_test, y_pred))

        # 5. Sauvegarde du modèle et du vectoriseur
        os.makedirs(os.path.dirname(Config.MODEL_PATH), exist_ok=True)
        joblib.dump(model, Config.MODEL_PATH)
        joblib.dump(vectorizer, Config.VECTORIZER_PATH)

        logger.info(f"Modèle sauvegardé dans {Config.MODEL_PATH}")
        logger.info(f"Vectoriseur sauvegardé dans {Config.VECTORIZER_PATH}")

    except Exception as e:
        logger.error(f"Erreur lors de l'entraînement: {e}")
        raise

if __name__ == "__main__":
    train_and_save_model()
