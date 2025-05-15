# src/ai/rag/llm_reasoner.py

import os
import logging
from transformers import pipeline
from huggingface_hub import login

logger = logging.getLogger(__name__)

class LocalLLMReasoner:
    def __init__(self, model_name="Qwen/Qwen2.5-Coder-3B", device="cpu"):
        self.model_name = model_name
        self.device = device
        self.llm = self._load_model()

    def _load_model(self):
        """Load local LLM"""
        try:
            hf_token = os.getenv("HUGGINGFACE_TOKEN")
            if hf_token and hf_token.startswith("hf_"):
                logger.info("[*] Logging into Hugging Face Hub...")
                login(token=hf_token)

            logger.info(f"[+] Loading LLM: {self.model_name} on {self.device.upper()}")
            return pipeline(
                "text-generation",
                model=self.model_name,
                trust_remote_code=True,
                device_map="auto"
            )
        except Exception as e:
            logger.warning(f"[!] LLM load failed: {e}")
            return None

    def explain(self, question: str, context: list) -> str:
        """Use LLM to generate grounded explanation"""
        context_str = "\n".join([doc["document"] for doc in context[:3]])
        prompt = f"""
You are Tephron AI – an intelligent assistant for AWS infrastructure.
Answer based on the following context:

{context_str}

Question:
{question}

Answer:
"""
        if self.llm:
            try:
                response = self.llm(prompt, max_new_tokens=200)[0]["generated_text"]
                logger.info(f"[+] LLM Response: {response[:80]}...")
                return response
            except Exception as e:
                logger.error(f"[!] LLM generation failed: {e}")

        return "[!] Unable to generate answer right now"