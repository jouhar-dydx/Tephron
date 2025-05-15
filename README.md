**Tephron AI** is an intelligent, modular, containerized AWS infrastructure assistant designed to act as a **junior AWS engineer bot**.

It scans, analyzes, and reasons about your AWS environment using:
- ✅ Boto3 for AWS SDK access
- ✅ PostgreSQL for structured data storage
- ✅ FAISS / RAG engine for grounded reasoning
- ✅ Local LLMs (Qwen, Mistral, Phi3) for decision support
- ✅ Slack integration for alerts and feedback

---

## 🧠 Vision & Mission

### 🎯 Mission
To build a **self-learning, observability-first tool** that helps engineering teams monitor, optimize, and improve their AWS infrastructure without relying on external SaaS tools or vendor lock-in.

### 🔭 Vision
Tephron will evolve into an **intelligent AWS assistant** that:
- Detects underutilized resources before they cost money
- Explains decisions based on AWS documentation (no hallucinations)
- Learns from human feedback via `/tephron confirm i-abc123`
- Recommends cost optimization strategies using real-time metrics
- Alerts engineers when anomalies are detected
- Is lightweight enough to run on a Raspberry Pi
- Uses only open-source tools — no Compose, no paid services

---

## 🛠️ Current Capabilities

As of this version, Tephron can:

### 1. ✅ Scan EC2 Instances Across All Regions
- Automatically detects all active AWS regions
- Scans running EC2 instances in parallel
- Collects metadata: ID, type, tags, state, region

### 2. ✅ Retrieve CloudWatch Metrics
- CPU Utilization
- Network In/Out
- Weekly averages stored per instance

### 3. ✅ Flag Underutilized Instances Using ML
- Trained using Isolation Forest
- Flags instances with low CPU (<10%) over time
- Stores results for future training

### 4. ✅ Store Structured Data in PostgreSQL
- Auto-migrates schema based on JSON input
- Ingests scan data with timestamps
- Enables historical tracking and reporting

### 5. ✅ Send Real-Time Alerts to Slack
- Sends message when underutilized instance found
- Supports `/tephron scan report`, `/tephron cost report` (coming soon)

### 6. ✅ Build FAISS Index of AWS Documentation
- Embeds AWS best practices for future reasoning
- Supports semantic search over knowledge base
- Will power `/tephron why i-abc123` command

### 7. ✅ Run Fully Inside Docker
- No hardcoded values
- Volume-based persistence (`data/output/`, `data/knowledge/`)
- Runs cleanly across multiple environments (CPU/GPU)

---

## 🚀 Getting Started
### 1. Clone the repo

```bash
git clone https://github.com/yourusername/Tephron.git 
cd Tephron

2. Create .env.prod file
touch config/.env.prod

Add these variables:

AWS_DEFAULT_REGION=us-east-1
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_ALERT_CHANNEL=#alerts
DB_HOST=tephron
DB_NAME=tephron
DB_USER=postgres
DB_PASSWORD=123
HUGGINGFACE_TOKEN=hf_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
RAG_LLM_MODEL=Qwen/Qwen2.5-Coder-3B

⚠️ Add this to .gitignore to avoid accidental exposure 

 3. Build base image
 sudo docker build -t tephron-base:latest -f docker/Dockerfile.base .

4. Run EC2 Scanner

sudo docker run --rm \
  -v $(pwd)/data:/app/data \
  -v ~/.aws:/root/.aws \
  tephron-base:latest \
  python /app/scripts/detect_and_alert_anomalies.py

This will:
Scan all AWS regions
Save structured JSON to /data/output/ec2/
Flag underutilized instances
Print findings to console

5. Ingest JSON Output to PostgreSQL
Start Postgres container:

sudo docker run -d \
  --name tephron-db \
  --network tephron-net \
  -e POSTGRES_DB=tephron \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=123 \
  postgres:15-alpine

Ingest data:

sudo docker run --rm \
  --network tephron-net \
  -v $(pwd)/data:/app/data \
  tephron-base:latest \
  python /app/scripts/ingest_json_to_postgres.py

6. Start Slack Bot

sudo docker run --rm \
  --network tephron-net \
  --env-file config/.env.prod \
  -v $(pwd)/data:/app/data \
  -v ~/.aws:/root/.aws \
  tephron-slack:latest

Now you’ll be able to:

Get alerts in Slack
Type /tephron help for available commands
Soon: ask “Why was this flagged?” using RAG + LLM

```

----

🧪 What It Can Do Right Now?.

🌍 Multi-region EC2 scanning
Scans across 20+ AWS regions

📈 CloudWatch metric collection
CPU, Network I/O tracked weekly

🤖 Anomaly detection
ML-powered underutilization flags

💾 Structured JSON output
With timestamps, ready for ingestion

🗃️ PostgreSQL integration
Schema-aware ingestion and querying

📢 Slack alerts
Real-time notifications

🧱 Modular architecture
Clean separation of concerns

🐳 Containerized deployment
No host-side changes needed

📁 Volume mapping
For persistent, portable data


----

🧩 Coming Soon

💰 Cost Explorer Integration - Forecast monthly,weekly and daily spend
🤝 Human-in-the-loop Feedback - /tephron confirm i-abc123 → store in DB
🧠 Local LLM Reasoning - Explain "why" using Qwen2.5 or Mistral (Choose whatever the model you want, but mind the computational cost!!!)
📚 RAG Engine - Ground answers in AWS documentation
🧮 Model Retraining - Improve accuracy using confirmed data
🧷 Command-Based Control - /tephron scan, /tephron cost report


🧑‍💻 Built by Engineer, for Engineers!!!

Tephron AI was built to solve real-world problems faced by AWS engineers:

❓ Why is this instance flagged?
💸 How much does this cost?
🚨 Should I downsize or delete?
🧪 How can we improve model accuracy?
With Tephron, you get:

✅ Open-source tooling
✅ Lightweight design
✅ Scalable architecture
✅ Enterprise-grade code
✅ No vendor lock-in

----

🧱 Architecture Overview -

Tephron AI – Intelligent AWS Infrastructure Assistant
│
├── Infrastructure Layer
│   └── Boto3 – AWS SDK access
│
├── Execution Layer
│   └── ThreadPoolExecutor – parallel scanning across regions
│
├── Output Layer
│   └── Structured JSON files in /data/output/ec2/
│
├── DB Layer
│   └── PostgreSQL – schema-aware ingestion + auto-migration
│
├── Intelligence Layer
│   ├── AnomalyDetector – Isolation Forest model
│   ├── FeedbackCollector – stores user input
│   └── ModelTrainer – improves accuracy over time
│
├── Knowledge Base Layer
│   ├── DocumentLoader – loads AWS best practices
│   └── FAISSVectorStore – enables semantic search
│
├── Reasoning Layer
│   └── LocalLLMReasoner – grounded explanations using Qwen/Mistral
│
├── Communication Layer
│   └── Slack Bot – alerts, commands, feedback
│
└── Observability Layer
    └── Structured logging + timestamped output


✅ Benefits ---

Tephron AI is an intelligent, lightweight, and open-source assistant that acts like a junior AWS engineer bot. It scans your AWS infrastructure in real-time, analyzes EC2 instances (Just for now, More on the way!!) across all active regions, fetches CloudWatch metrics (CPU,GPU,Memory and Network I/O), and estimates costs dynamically using the AWS Pricing API — no hardcoded values, no vendor lock-in, no unnecessary dependencies. Built with Python, Docker, PostgreSQL, and powered by local LLMs and RAG-based reasoning, Tephron delivers:

✅ AI-powered insights , not just alerts — suggests cost savings, flags underutilized resources, and reasons about anomalies
✅ Modular design — swap out components without breaking the system
✅ Container-first architecture — runs cleanly in Docker with zero Compose dependency
✅ Enterprise security — read-only IAM policies, structured logging, and secret handling via environment variables
✅ Self-improving logic — learns from human feedback and historical data
✅ Historical tracking — stores every scan in PostgreSQL for ML training and trend analysis
Tephron isn't just monitoring your cloud — it’s building intelligence around it. With built-in Slack integration, FAISS-backed RAG engine, and anomaly detection using Isolation Forests, this is observability reimagined: lightweight, scalable, and fully explainable.



