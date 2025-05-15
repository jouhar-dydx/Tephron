# src/ai/reasoning_engine.py
from transformers import pipeline
from core.utils import save_json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ReasoningEngine:
    def __init__(self, rag_engine=None, model_name="Qwen/Qwen2.5", device="cpu"):
        self.rag = rag_engine
        try:
            self.llm = pipeline("text-generation", model=model_name, device=device)
            logger.info(f"[+] Loaded LLM: {model_name} on {device.upper()}")
        except Exception as e:
            logger.error(f"[!] Failed to load LLM: {e}")
            self.llm = None

    def explain(self, prompt, k=3):
        context = self._get_context(prompt, k)
        full_prompt = self._build_prompt(prompt, context)
        if not self.llm:
            return {"error": "LLM not available"}
        try:
            response = self.llm(full_prompt, max_new_tokens=200)[0]["generated_text"]
            return {
                "timestamp": datetime.now().isoformat(),
                "prompt": prompt,
                "context": context,
                "response": response
            }
        except Exception as e:
            logger.error(f"[!] LLM generation failed: {e}")
            return {"error": str(e)}

    def _get_context(self, query, k=3):
        if self.rag:
            return self.rag.search(query, k=k)
        return []

    def _build_prompt(self, question, context):
        context_str = "\n".join([f"{doc['score']}: {doc['document']}" for doc in context])
        return f"""
You are an AWS engineer bot analyzing EC2 instances.
Answer based on the following context:

{context_str}

Question:
{question}
Answer:
"""