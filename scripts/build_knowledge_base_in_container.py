# scripts/build_knowledge_base_in_container.py

import os
import logging
from src.ai.rag.document_loader import AWSDocumentLoader
from src.ai.rag.vector_store import FAISSVectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("[*] Building AWS knowledge base inside container")

    # Ensure knowledge base exists
    kb_dir = "/app/data/knowledge/aws/"
    if not os.path.exists(kb_dir):
        logger.warning(f"[!] Knowledge base not found at {kb_dir}")
        logger.info("[+] Creating empty knowledge base folder")
        os.makedirs(kb_dir, exist_ok=True)

        # Add default file
        default_file = os.path.join(kb_dir, "ec2_best_practices.txt")
        with open(default_file, "w") as f:
            f.write("""
Underutilized EC2 instances are those that:
- Have CPU utilization < 10% over 3+ days
- Are running in production but used for dev/test
- Can be replaced with Lambda or Fargate

Recommendation:
- Consider downsizing or switching to Spot
- Use Cost Explorer to forecast monthly spend
""")
        logger.info(f"[+] Created sample file: {default_file}")

    # Load documents
    loader = AWSDocumentLoader(kb_dir)
    docs = loader.load_documents()
    if not docs:
        logger.warning("[!] No documents loaded into FAISS")
        return

    # Build FAISS index
    vs = FAISSVectorStore(index_path="/app/data/embeddings/aws_index.bin")
    vs.add_documents(docs)
    vs.save_index()

if __name__ == "__main__":
    main()