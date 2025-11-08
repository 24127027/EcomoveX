import numpy as np
from sklearn.cluster import KMeans

def cluster_users(user_embeddings, n_clusters=5):
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(np.array(user_embeddings))
    return clusters
