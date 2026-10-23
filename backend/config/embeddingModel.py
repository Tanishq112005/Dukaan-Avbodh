import os
import numpy as np

class DummyEmbedder:
    def encode(self, texts, **kwargs):
        if isinstance(texts, str):
            return np.zeros(384, dtype=np.float32)
        return np.zeros((len(texts), 384), dtype=np.float32)

class EmbeddingModel:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def getModel(self):
        if self._model is not None:
            return self._model
        
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        except Exception as e:
            print(f"[WARNING] Could not load SentenceTransformer ({e}). Falling back to DummyEmbedder.")
            self._model = DummyEmbedder()
            
        return self._model

    def get_model(self):
        return self.getModel()

embeddingModel = EmbeddingModel()
