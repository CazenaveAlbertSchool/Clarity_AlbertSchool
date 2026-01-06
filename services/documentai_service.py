from google.cloud import documentai_v1 as documentai
from google.api_core.exceptions import GoogleAPICallError
from config import PROJECT_ID, LOCATION, DOCUMENTAI_PROCESSOR_ID

def process_document(text):
    try:
        client = documentai.DocumentProcessorServiceClient()
        name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{DOCUMENTAI_PROCESSOR_ID}"
        document = {"content": text, "mime_type": "text/plain"}
        request = {"name": name, "raw_document": document}
        result = client.process_document(request=request)

        # Extraction des entités et des paires clé-valeur (si disponibles)
        entities = []
        for entity in result.document.entities:
            entities.append({
                "type": entity.type_,
                "text": entity.mention_text,
                "confidence": entity.confidence  # Si disponible
            })
        return {"entities": entities, "full_text": result.document.text}
    except GoogleAPICallError as e:
        print(f"Erreur Document AI: {e}")
        return None
