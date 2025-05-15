# src/ai/rag_engine.py
import os
import json
import logging
from sentence_transformers import SentenceTransformer
from faiss import IndexFlatL2
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2", index_path=None):
        self.model = SentenceTransformer(model_name)
        self.index = IndexFlatL2(self.model.get_sentence_embedding_dimension())
        self.documents = []
        self.doc_id_to_index = {}
        self._load_or_build_index(index_path)

    def _load_or_build_index(self, index_path=None):
        if index_path and os.path.exists(index_path):
            logger.info(f"[+] Loading FAISS index from {index_path}")
            self.index = faiss.read_index(index_path)
            with open(index_path.replace(".index", ".docs.json"), 'r') as f:
                self.documents = json.load(f)
            logger.info(f"[+] Loaded {len(self.documents)} documents into FAISS")
        else:
            logger.info("[+] Created new FAISS index")

    def add_documents(self, docs):
        """
        Add documents to FAISS index
        docs: List of strings or dict-like objects
        """
        texts = [str(doc) for doc in docs]
        embeddings = self.model.encode(texts)
        self.index.add(np.array(embeddings).astype(np.float32))
        self.documents.extend(docs)
        logger.info(f"[+] Added {len(docs)} document(s) to FAISS index")

    def search(self, query, k=5):
        """
        Search FAISS index for top-k relevant documents
        """
        query_vector = self.model.encode([query])
        D, I = self.index.search(np.array(query_vector).astype(np.float32), k=k)
        results = [{"score": float(D[0][i]), "document": self.documents[i]} for i in I[0]]
        logger.info(f"[+] Retrieved top {k} documents for query: '{query}'")
        return results