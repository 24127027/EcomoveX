import sys
import os

# Add backend folder to path BEFORE any model imports
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, backend_path)

import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import User, UserActivity, Activity
from models.cluster import Cluster
from database.db import Base

# Import refactored services
from services.embedding_service import embed_user, embed_destination, build_all_destination_embeddings
from utils.faiss_utils import build_index
from services.cluster_service import assign_user_to_cluster, compute_cluster_popularity
from services.recommendation_service import (
    recommend_for_cluster_hybrid,
    recommend_for_cluster_similarity,
    recommend_for_cluster_popularity
)

# -----------------------------
# Setup in-memory SQLite DB
# -----------------------------
engine = create_engine("sqlite:///:memory:", echo=False)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()
Base.metadata.create_all(bind=engine)

# -----------------------------
# Create dummy users
# -----------------------------
users = []
for i in range(5):
    u = User(
        id=i+1,
        username=f"user{i+1}",
        email=f"user{i+1}@example.com",
        password="hashed_password",
        temp_min=15,
        temp_max=30,
        budget_min=100,
        budget_max=500,
        eco_point=random.randint(0,10)
    )
    session.add(u)
    users.append(u)
session.commit()

# -----------------------------
# Create dummy destinations
# -----------------------------
destinations = []
for i in range(10):
    d = {
        "id": f"dest{i+1}",
        "name": f"Destination {i+1}",
        "tags": ["beach", "mountain"] if i % 2 == 0 else ["city", "museum"],
        "description": f"A lovely place number {i+1}"
    }
    destinations.append(d)

# -----------------------------
# Create a dummy cluster
# -----------------------------
cluster = Cluster(id=1, name="Cluster1", algorithm="kmeans")
session.add(cluster)
session.commit()

# Assign users to cluster
for u in users:
    assign_user_to_cluster(u.id, cluster.id, session)

# -----------------------------
# Create dummy user activities
# -----------------------------
activities = [Activity.save_destination, Activity.search_destination, Activity.review_destination]
for u in users:
    for d in destinations:
        act = UserActivity(user_id=u.id, destination_id=d["id"], activity=random.choice(activities))
        session.add(act)
session.commit()

# -----------------------------
# Build destination embeddings
# -----------------------------
print("Building destination embeddings...")
build_all_destination_embeddings(session, destinations)

print("Building FAISS index...")
build_index(session)

# -----------------------------
# Test recommendations
# -----------------------------
print("\n=== Hybrid Recommendations ===")
hybrid_results = recommend_for_cluster_hybrid(cluster.id, session, k=5)
for r in hybrid_results:
    print(f"  {r}")

print("\n=== Similarity-Only Recommendations ===")
similarity_results = recommend_for_cluster_similarity(cluster.id, session, k=5)
for r in similarity_results:
    print(f"  {r}")

print("\n=== Popularity-Only Recommendations ===")
popularity_results = recommend_for_cluster_popularity(cluster.id, session, k=5)
for r in popularity_results:
    print(f"  {r}")

print("\n✓ Test completed successfully!")