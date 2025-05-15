# Tephron AI – Intelligent AWS Infrastructure Assistant

Tephron AI is an intelligent assistant that acts as a junior AWS engineer. It monitors, analyzes, and reports on AWS infrastructure using AI, ML, and observability tools.

🔧 Features:
- Monitors AWS resources (EC2, RDS, Lambda, CloudWatch, Cost Explorer)
- Detects underutilized, orphaned, or overused resources
- Analyzes logs and detects anomalies
- Cost forecasting and optimization
- Human-in-the-loop via Slack
- Lightweight, open-source, and fully customizable

🛠 Built with:
- Python
- Boto3
- PostgreSQL
- FAISS / LanceDB
- Docker
- Slack SDK

📦 Modular Architecture:
- Core: Logging, Utilities, DB Handler
- AWS: EC2, CloudWatch, Cost Explorer
- AI: Anomaly Detection, RAG Engine
- Slack: Alerts, Commands, Feedback

## 🚀 Getting Started

To run Tephron:

1. Clone the repo
2. Set up AWS credentials (`~/.aws/credentials`)
3. Run:
   ```bash
   cd Tephron
   chmod +x scripts/start_tephron.sh
   ./scripts/start_tephron.sh

📦 Requirements
Ensure you have:

Python 3.10+
Docker
AWS CLI configured
PostgreSQL (optional)
