"""
Service pour classifier les factures et extraire les dates de paiement.
"""
import re
import logging
from datetime import datetime
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mots-clés pour identifier les dates de paiement
PAYMENT_DATE_KEYWORDS = [
    'date de paiement', 'date paiement', 'paiement le', 'payable le',
    'à payer le', 'échéance', 'due date', 'payment date', 'pay by',
    'date limite', 'date d\'échéance', 'échéance le', 'payable avant',
    'à régler le', 'règlement le', 'date règlement'
]

# Mots-clés pour identifier une facture
INVOICE_KEYWORDS = [
    'facture', 'invoice', 'bill', 'note de', 'avoir', 'credit note',
    'devis', 'quote', 'quotation', 'référence', 'réf', 'ref', 'n°', 'no',
    'montant', 'total', 'tva', 't.t.c', 'h.t', 'ht', 'ttc', 'net à payer',
    'société', 'siret', 'siren', 'tva intracommunautaire'
]

def classify_document(text, entities=None):
    """
    Classifie un document pour déterminer s'il s'agit d'une facture.
    
    Args:
        text: Texte extrait du document
        entities: Liste d'entités extraites par DocumentAI (optionnel)
    
    Returns:
        dict avec:
            - is_invoice: bool
            - confidence: float (0.0 à 1.0)
            - invoice_type: str ('invoice', 'quote', 'credit_note', 'unknown')
            - indicators: list des indicateurs trouvés
    """
    if not text:
        return {
            "is_invoice": False,
            "confidence": 0.0,
            "invoice_type": "unknown",
            "indicators": []
        }
    
    text_lower = text.lower()
    indicators = []
    score = 0.0
    invoice_type = "unknown"
    
    # Vérifie les mots-clés de facture
    invoice_matches = sum(1 for keyword in INVOICE_KEYWORDS if keyword in text_lower)
    if invoice_matches > 0:
        score += min(invoice_matches * 0.15, 0.6)  # Max 0.6 pour les mots-clés
        indicators.append(f"{invoice_matches} mots-clés de facture trouvés")
    
    # Vérifie les entités DocumentAI
    if entities:
        entity_types = [e.get('type', '') for e in entities]
        # Types d'entités typiques des factures
        invoice_entity_types = [
            'invoice_id', 'invoice_date', 'total_amount', 'tax_amount',
            'vendor_name', 'vendor_address', 'purchase_order', 'line_item',
            'amount', 'date', 'organization', 'address', 'phone_number'
        ]
        entity_matches = sum(1 for et in entity_types if any(iet in et.lower() for iet in invoice_entity_types))
        if entity_matches > 0:
            score += min(entity_matches * 0.1, 0.3)  # Max 0.3 pour les entités
            indicators.append(f"{entity_matches} entités de facture détectées")
    
    # Vérifie la présence de montants (€, EUR, chiffres avec décimales)
    amount_pattern = r'\d+[.,]\d{2}\s*(?:€|EUR|euros?)'
    if re.search(amount_pattern, text, re.IGNORECASE):
        score += 0.2
        indicators.append("Montants monétaires détectés")
    
    # Vérifie la présence de numéros de facture
    invoice_number_patterns = [
        r'facture\s*n[°o]?\s*:?\s*[\w-]+',
        r'invoice\s*n[°o]?\s*:?\s*[\w-]+',
        r'réf[érence]*\s*:?\s*[\w-]+',
        r'ref[erence]*\s*:?\s*[\w-]+'
    ]
    for pattern in invoice_number_patterns:
        if re.search(pattern, text_lower):
            score += 0.1
            indicators.append("Numéro de facture détecté")
            break
    
    # Détermine le type de document
    if 'devis' in text_lower or 'quote' in text_lower or 'quotation' in text_lower:
        invoice_type = "quote"
    elif 'avoir' in text_lower or 'credit note' in text_lower:
        invoice_type = "credit_note"
    elif score > 0.5:
        invoice_type = "invoice"
    
    is_invoice = score >= 0.4  # Seuil de confiance
    
    return {
        "is_invoice": is_invoice,
        "confidence": min(score, 1.0),
        "invoice_type": invoice_type,
        "indicators": indicators
    }

def extract_payment_date(text, entities=None):
    """
    Extrait la date de paiement depuis le texte d'une facture.
    
    Args:
        text: Texte extrait du document
        entities: Liste d'entités extraites par DocumentAI (optionnel)
    
    Returns:
        dict avec:
            - payment_date: datetime ou None
            - date_string: str (texte original de la date)
            - confidence: float (0.0 à 1.0)
            - method: str ('keyword', 'entity', 'pattern')
    """
    if not text:
        return {
            "payment_date": None,
            "date_string": None,
            "confidence": 0.0,
            "method": None
        }
    
    text_lower = text.lower()
    best_match = None
    best_confidence = 0.0
    method = None
    
    # Méthode 1: Cherche dans les entités DocumentAI
    if entities:
        for entity in entities:
            entity_type = entity.get('type', '').lower()
            if 'payment' in entity_type or 'due' in entity_type or 'échéance' in entity_type:
                date_text = entity.get('text', '')
                try:
                    parsed_date = date_parser.parse(date_text, fuzzy=True, dayfirst=True)
                    if parsed_date:
                        return {
                            "payment_date": parsed_date,
                            "date_string": date_text,
                            "confidence": 0.9,
                            "method": "entity"
                        }
                except (ValueError, TypeError):
                    continue
    
    # Méthode 2: Cherche avec des mots-clés autour des dates
    for keyword in PAYMENT_DATE_KEYWORDS:
        # Pattern pour trouver le mot-clé suivi d'une date
        pattern = rf'{re.escape(keyword)}\s*:?\s*([0-9]{{1,2}}[/\-\.][0-9]{{1,2}}[/\-\.][0-9]{{2,4}}|[0-9]{{1,2}}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+[0-9]{{4}}|[0-9]{{1,2}}\s+(?:jan|fév|mar|avr|mai|jun|jul|aoû|sep|oct|nov|déc)[a-z]*\s+[0-9]{{4}})'
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        
        for match in matches:
            date_str = match.group(1)
            try:
                parsed_date = date_parser.parse(date_str, fuzzy=True, dayfirst=True)
                if parsed_date:
                    # Vérifie que la date est dans le futur ou récent (pas trop ancienne)
                    if parsed_date.year >= datetime.now().year - 1:
                        return {
                            "payment_date": parsed_date,
                            "date_string": date_str,
                            "confidence": 0.85,
                            "method": "keyword"
                        }
            except (ValueError, TypeError):
                continue
    
    # Méthode 3: Cherche des patterns de dates proches de mots-clés de paiement
    # Cherche dans un contexte de 50 caractères autour des mots-clés
    for keyword in PAYMENT_DATE_KEYWORDS:
        keyword_positions = [m.start() for m in re.finditer(re.escape(keyword), text_lower)]
        for pos in keyword_positions:
            # Extrait 100 caractères après le mot-clé
            context = text[pos:pos+100]
            # Cherche des dates dans ce contexte
            date_patterns = [
                r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}',
                r'\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}',
                r'\d{1,2}\s+(?:jan|fév|mar|avr|mai|jun|jul|aoû|sep|oct|nov|déc)[a-z]*\s+\d{4}'
            ]
            
            for pattern in date_patterns:
                date_matches = re.finditer(pattern, context, re.IGNORECASE)
                for date_match in date_matches:
                    date_str = date_match.group(0)
                    try:
                        parsed_date = date_parser.parse(date_str, fuzzy=True, dayfirst=True)
                        if parsed_date and parsed_date.year >= datetime.now().year - 1:
                            if not best_match or parsed_date > best_match:
                                best_match = parsed_date
                                best_confidence = 0.7
                                method = "pattern"
                    except (ValueError, TypeError):
                        continue
    
    # Méthode 4: Si aucune date de paiement trouvée, cherche la date de facture + délai standard (30 jours)
    if not best_match:
        invoice_date = extract_invoice_date(text, entities)
        if invoice_date:
            # Ajoute 30 jours par défaut
            best_match = invoice_date + relativedelta(days=30)
            best_confidence = 0.5
            method = "estimated"
            logger.info("Date de paiement estimée (date facture + 30 jours)")
    
    return {
        "payment_date": best_match,
        "date_string": best_match.strftime("%d/%m/%Y") if best_match else None,
        "confidence": best_confidence,
        "method": method
    }

def extract_invoice_date(text, entities=None):
    """
    Extrait la date de la facture depuis le texte.
    
    Args:
        text: Texte extrait du document
        entities: Liste d'entités extraites par DocumentAI (optionnel)
    
    Returns:
        datetime ou None
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Cherche dans les entités DocumentAI
    if entities:
        for entity in entities:
            entity_type = entity.get('type', '').lower()
            if 'invoice_date' in entity_type or 'date' in entity_type:
                date_text = entity.get('text', '')
                try:
                    return date_parser.parse(date_text, fuzzy=True, dayfirst=True)
                except (ValueError, TypeError):
                    continue
    
    # Cherche avec des mots-clés
    date_keywords = ['date facture', 'facture du', 'invoice date', 'date:', 'le']
    for keyword in date_keywords:
        pattern = rf'{re.escape(keyword)}\s*:?\s*([0-9]{{1,2}}[/\-\.][0-9]{{1,2}}[/\-\.][0-9]{{2,4}})'
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            date_str = match.group(1)
            try:
                return date_parser.parse(date_str, fuzzy=True, dayfirst=True)
            except (ValueError, TypeError):
                continue
    
    return None

def process_invoice(text, entities=None):
    """
    Traite une facture complète : classification + extraction de la date de paiement.
    
    Args:
        text: Texte extrait du document
        entities: Liste d'entités extraites par DocumentAI (optionnel)
    
    Returns:
        dict avec classification et date de paiement
    """
    classification = classify_document(text, entities)
    payment_info = extract_payment_date(text, entities) if classification["is_invoice"] else {
        "payment_date": None,
        "date_string": None,
        "confidence": 0.0,
        "method": None
    }
    
    return {
        "classification": classification,
        "payment_date": payment_info
    }
