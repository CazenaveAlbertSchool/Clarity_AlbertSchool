
from google.cloud import documentai_v1 as documentai
from config import PROJECT_ID, LOCATION, DOCUMENTAI_PROCESSOR_ID

def process_document(text):
    client = documentai.DocumentProcessorServiceClient()
    name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{DOCUMENTAI_PROCESSOR_ID}"
    document = {"content": text, "mime_type": "text/plain"}
    request = {"name": name, "raw_document": document}
    result = client.process_document(request=request)
    return {"entities": [{"type": e.type_, "text": e.mention_text} for e in result.document.entities]}
