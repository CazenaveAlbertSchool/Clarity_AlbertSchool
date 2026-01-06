from google.cloud import firestore
from google.api_core.exceptions import GoogleAPICallError

def save_result(file_name, text, document_data):
    try:
        db = firestore.Client()
        doc_ref = db.collection('documents').document()
        doc_ref.set({
            'file_name': file_name,
            'text': text[:10000],  # Limite la taille du texte stocké si nécessaire
            'entities': document_data.get('entities', []),
            'document_type': document_data.get('document_type', 'unknown'),
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        return doc_ref.id
    except GoogleAPICallError as e:
        print(f"Erreur Firestore: {e}")
        return None
