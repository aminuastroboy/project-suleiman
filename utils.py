import numpy as np
from PIL import Image, ImageOps
import io

def image_to_embedding(img: Image.Image):
    size = (64,64)
    img = ImageOps.fit(img.convert("L"), size)
    arr = np.asarray(img).astype("float32")/255.0
    return arr.flatten()

def compare_embeddings(emb, stored_bytes, threshold=0.85):
    stored = np.frombuffer(stored_bytes, dtype="float32")
    emb = emb.flatten()
    sim = np.dot(emb, stored) / (np.linalg.norm(emb)*np.linalg.norm(stored))
    return sim > threshold
