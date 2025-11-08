from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_destination(destination):
    text = f"{destination.name} {' '.join(destination.tags)}"
    return model.encode(text).tolist()
