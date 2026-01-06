
from flask import Flask, render_template, request, jsonify
from services.drive_service import list_files, download_file
from services.vision_service import detect_text
from services.documentai_service import process_document
from services.firestore_service import save_result
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    file_id = request.json.get('file_id')
    file_name = request.json.get('file_name')
    
    # 1. Télécharger le fichier depuis Google Drive
    file_path = download_file(file_id, file_name)
    
    # 2. Extraire le texte avec Vision API
    text = detect_text(file_path)
    
    # 3. Classifier avec Document AI
    document_data = process_document(text)
    
    # 4. Sauvegarder dans Firestore
    doc_id = save_result(file_name, text, document_data)
    
    return jsonify({"status": "success", "document_id": doc_id})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
