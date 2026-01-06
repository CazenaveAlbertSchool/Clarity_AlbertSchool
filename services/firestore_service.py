
from google.cloud import firestore

def save_result(file_name, text, document_data):
    db = firestore.Client()
    doc_ref = db.collection('documents').document()
    doc_ref.set({
        'file_name': file_name,
        'text': text,
        'entities': document_data['entities'],
        'timestamp': firestore.SERVER_TIMESTAMP
    })
    return doc_ref.id
