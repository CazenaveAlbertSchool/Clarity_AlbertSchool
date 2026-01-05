from utils.ocr_utils import extract_expiry_date
from datetime import datetime

def test_extract_expiry_date():
    text_with_date = "Date d'expiration: 31/12/2025"
    expiry_date = extract_expiry_date(text_with_date)
    assert expiry_date == datetime(2025, 12, 31)

def test_extract_expiry_date_no_date():
    text = "Aucune date ici"
    assert extract_expiry_date(text) is None
