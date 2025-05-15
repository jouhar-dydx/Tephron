# scripts/start_rag_server.py

import os
import logging
from src.ai.rag.rag_engine import RAGEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("[*] Starting Tephron AI RAG Server")

    rag_data_dir = "/app/data/knowledge/aws/"
    model_path = os.getenv("RAG_LLM_MODEL", "Qwen/Qwen2.5-Coder-3B")
    output_model_path = "/app/models/qwen2_5_coder_3b"

    # Step 1: Ensure knowledge base exists
    if not os.path.exists(rag_data_dir):
        os.makedirs(rag_data_dir, exist_ok=True)

        # Add default AWS underutilization policy
        with open(os.path.join(rag_data_dir, "ec2_best_practices.txt"), "w") as f:
            f.write("""
Underutilized EC2 instances are defined as those that:
- Have CPU utilization < 10% over 3+ days
- Are on-demand when Spot could be used
- Can be replaced with Lambda or Fargate

Recommendation:
- Consider downsizing or switching to Spot
- Use Cost Explorer to forecast monthly spend
""")
        logger.info(f"[+] Created sample knowledge base at {rag_data_dir}")

    # Step 2: Download Qwen2.5 model inside container
    from src.ai.rag.llm_reasoner import LocalLLMReasoner

    logger.info(f"[+] Using model name: {model_path}")
    reasoner = LocalLLMReasoner(model_path=output_model_path)

    # Step 3: Save model locally in mounted volume
    logger.info(f"[+] Saving model to {output_model_path}")
    reasoner.save_local(output_model_path)

if __name__ == "__main__":
    main()