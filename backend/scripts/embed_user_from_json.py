from pathlib import Path
import sys
from collections import Counter

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Import the patched service (patch is applied automatically)
from services import embedding_service

# Example user JSON
sample_user = {
    "id": 42,
    "username": "traveler_joe",
    "temp_min": 15.0,
    "temp_max": 25.0,
    "budget_min": 200.0,
    "budget_max": 800.0,
    "eco_point": 120,
    "rank": "Gold",
    "activities": [
        {"destination_id": 101, "activity": "save destination"},
        {"destination_id": 101, "activity": "save destination"},
        {"destination_id": 202, "activity": "search destination"},
        {"destination_id": 303, "activity": "review destination"},
        {"destination_id": 202, "activity": "search destination"},
    ]
}

def build_user_text_from_json(user_json: dict) -> str:
    parts = []
    if user_json.get("temp_min") is not None and user_json.get("temp_max") is not None:
        parts.append(f"prefers temperature between {user_json['temp_min']} and {user_json['temp_max']} degrees")
    if user_json.get("budget_min") is not None and user_json.get("budget_max") is not None:
        parts.append(f"budget range {user_json['budget_min']} to {user_json['budget_max']}")
    activities = user_json.get("activities", [])
    activity_counter = Counter(a["activity"] for a in activities)
    for act, cnt in activity_counter.items():
        parts.append(f"{act} {cnt} times")
    if user_json.get("eco_point"):
        parts.append(f"eco-conscious with {user_json['eco_point']} eco points")
    if user_json.get("rank"):
        parts.append(f"travel experience level {user_json['rank']}")
    if not parts:
        parts.append(f"user {user_json.get('username','unknown')}")
    return " ".join(parts)

def embed_and_print(user_json: dict):
    text = build_user_text_from_json(user_json)
    embedding = embedding_service.model.encode(text).tolist()
    print("=" * 60)
    print("User Embedding Preview")
    print("=" * 60)
    print(f"User ID: {user_json.get('id')}")
    print(f"Username: {user_json.get('username')}")
    print(f"\nSummary text used for embedding:")
    print(f"  {text}")
    print(f"\nEmbedding length: {len(embedding)}")
    preview = ', '.join(f"{v:.5f}" for v in embedding[:8])
    print(f"Embedding (first 8 values): [{preview}, ...]")
    print("=" * 60)

if __name__ == "__main__":
    embed_and_print(sample_user)