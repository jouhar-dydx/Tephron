# src/ai/rag/document_loader.py

import os
import logging
from typing import Dict, Any, List, Optional, Union, Tuple, TypeVar

logger = logging.getLogger(__name__)
DOCUMENT_DIR = "/app/data/knowledge/aws/"

class AWSDocumentLoader:
    def __init__(self, directory: str = DOCUMENT_DIR):
        self.directory = directory

    def load_documents(self) -> List[str]:
        """Load all AWS documentation files from local folder"""
        try:
            if not os.path.exists(self.directory):
                logger.warning(f"[!] Knowledge base not found at {self.directory}")
                return []

            files = [f for f in os.listdir(self.directory) if f.endswith(".txt")]
            logger.info(f"[+] Found {len(files)} AWS doc files")

            documents = []
            for filename in files:
                with open(os.path.join(self.directory, filename), 'r') as f:
                    content = f.read().strip()
                    # Split by paragraphs
                    documents.extend(content.split("\n\n"))

            logger.info(f"[+] Loaded {len(documents)} document chunks")
            return documents
        except Exception as e:
            logger.error(f"[!] Failed to load documents: {e}")
            return []