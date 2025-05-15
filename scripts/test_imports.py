# scripts/test_imports.py

import sys
print("[+] PYTHONPATH:", sys.path)

try:
    from src.aws.ec2.scanner import get_all_regions, EC2Scanner
    print("[+] Imports successful")
except ImportError as e:
    print(f"[!] ImportError: {e}")