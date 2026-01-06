import pytest
from app import app
from Clarity_MVP.config import Config

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Clarity" in response.data

def test_upload_document(client):
    # Test avec un fichier mock
    data = {
        'document': (open('tests/sample.pdf', 'rb'), 'sample.pdf')
    }
    response = client.post("/", data=data, content_type='multipart/form-data')
    assert response.status_code == 302  # Redirection après upload
