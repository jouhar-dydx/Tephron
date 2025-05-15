# src/ai/rag/vector_store.py

import os
import faiss
import numpy as np
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class FAISSVectorStore:
    def __init__(self, model_name="all-MiniLM-L6-v2", index_path="/app/data/embeddings/aws_ec2_knowledge.index"):
        self.model_name = model_name
        self.index_path = index_path
        self.dimension = 384  # all-MiniLM-L6-v2 output size
        self.model = SentenceTransformer(model_name)
        self.documents = self.load_documents()
        self.index = self.build_index()

    def load_documents(self):
        """Load AWS documentation for embedding"""
        from src.ai.rag.document_loader import AWSDocumentLoader
        loader = AWSDocumentLoader("/app/data/knowledge/aws/")
        return loader.load_documents()

    def build_index(self):
        """Build FAISS index from loaded documents"""
        try:
            embeddings = self.model.encode(self.documents)
            index = faiss.IndexFlatL2(self.dimension)
            index.add(np.array(embeddings).astype(np.float32))
            faiss.write_index(index, self.index_path)
            logger.info(f"[+] FAISS index saved to {self.index_path}")
            return index
        except Exception as e:
            logger.error(f"[!] Failed to build FAISS index: {e}")
            return faiss.read_index(self.index_path)

    def search(self, query: str, k=5) -> list:
        """Search FAISS index using semantic similarity"""
        try:
            query_emb = self.model.encode([query])
            D, I = self.index.search(np.array(query_emb).astype(np.float32), k=k)
            results = [{"score": float(D[0][i]), "document": self.documents[I[0][i]]} for i in range(k)]
            logger.info(f"[+] Retrieved top {k} documents for '{query}'")
            return results
        except Exception as e:
            logger.error(f"[!] FAISS search failed: {e}")
            return []