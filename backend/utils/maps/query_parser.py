import re
import spacy
from spacy.matcher import PhraseMatcher

nlp = spacy.load("en_core_web_sm")

POI_TYPES = ["cafe", "coffee shop", "restaurant", "park", "coworking", "library", "ev charger"]
ECO_TERMS = ["vegan", "organic", "eco-friendly", "zero waste", "plastic-free",
             "bike-friendly", "recycling", "compost", "plants", "greenery"]
TIME_TERMS = ["open now", "24/7", "open late", "open early"]
MOBILITY_TERMS = ["walkable", "near", "around", "within walking distance", "bike-friendly"]

PRICE_PATTERNS = [
    r"under (\d+)(k|k vnd| vnd)?",
    r"<(\d+)(k|k vnd| vnd)?",
    r"less than (\d+)(k|k vnd| vnd)?"
]

phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
phrase_matcher.add("POI", [nlp.make_doc(t) for t in POI_TYPES])
phrase_matcher.add("ECO", [nlp.make_doc(t) for t in ECO_TERMS])
phrase_matcher.add("MOBILITY", [nlp.make_doc(t) for t in MOBILITY_TERMS])
phrase_matcher.add("TIME", [nlp.make_doc(t) for t in TIME_TERMS])

def extract_price(text):
    text = text.lower()
    for pat in PRICE_PATTERNS:
        m = re.search(pat, text)
        if m:
            return {"price_max": int(m.group(1)) * 1000}
    return None

def extract_district(text):
    text = text.lower()
    district_pattern = r"\b(?:district|d|q|quận)\s*\.?(\d+)\b"
    m = re.search(district_pattern, text)
    return f"District {m.group(1)}" if m else None

def parse_query(text):
    doc = nlp(text)
    result = {
        "category": None,
        "eco_tags": [],
        "location": None,
        "filters": {"open_now": False, "walkable": False},
        "price": None
    }

    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC", "FAC"] and not result["location"]:
            result["location"] = ent.text
    
    if not result["location"]:
        district = extract_district(text)
        if district:
            result["location"] = district

    matches = phrase_matcher(doc)
    for match_id, start, end in matches:
        label = nlp.vocab.strings[match_id]
        span = doc[start:end].text.lower()

        if label == "POI" and not result["category"]:
            result["category"] = span
        elif label == "ECO":
            result["eco_tags"].append(span)
        elif label == "MOBILITY":

            text_lower = text.lower()
            if span == "near" and result["location"]:

                near_pattern = rf"\bnear\s+{re.escape(result['location'].lower())}"
                if re.search(near_pattern, text_lower):

                    continue
            result["filters"]["walkable"] = True
        elif label == "TIME" and span == "open now":
            result["filters"]["open_now"] = True

    result["price"] = extract_price(text)

    return result