# scripts/download_qwen_model.py

import os
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "Qwen/Qwen2.5-Coder-3B"
LOCAL_PATH = "/app/models/qwen2_5_coder_3b"

def main():
    print(f"[*] Downloading model: {MODEL_NAME}")
    os.makedirs(LOCAL_PATH, exist_ok=True)

    print(f"[+] Saving model to {LOCAL_PATH}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, trust_remote_code=True)

    tokenizer.save_pretrained(LOCAL_PATH)
    model.save_pretrained(LOCAL_PATH)

    print(f"[+] Model saved at {LOCAL_PATH}")

if __name__ == "__main__":
    main()