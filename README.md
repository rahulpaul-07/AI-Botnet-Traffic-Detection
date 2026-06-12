# 🛡️ SENTINEL AI - Production-Grade Botnet Detection System

[![CI](https://github.com/rahulpaul-07/AI-Botnet-Traffic-Detection/actions/workflows/ci.yml/badge.svg)](https://github.com/rahulpaul-07/AI-Botnet-Traffic-Detection/actions/workflows/ci.yml) [![Docker Compose Ready](https://github.com/rahulpaul-07/AI-Botnet-Traffic-Detection/actions/workflows/ci.yml/badge.svg)](https://github.com/rahulpaul-07/AI-Botnet-Traffic-Detection/actions/workflows/ci.yml)

## 🚀 Overview
SENTINEL AI is a high-fidelity Network Intrusion Detection System (NIDS) designed to identify botnet traffic in real-time. Built with a modular enterprise architecture, it leverages advanced Machine Learning (XGBoost/LightGBM) and real-time packet inspection (Scapy).

## 🧭 Getting Started
1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Initialize and train models (if missing):
```bash
python init_project.py
```
3. Start the full stack:
```bash
python run_all.py
```

> Or run the project in Docker containers:
> ```bash
docker compose up --build
> ```

4. Open the dashboard at `http://localhost:8501` and API docs at `http://localhost:8000/docs`

## 📂 Project Structure

## 📂 Project Structure
- `backend_api/`: FastAPI server for inference and logging.
- `frontend_streamlit/`: Professional cybersecurity dashboard.
- `realtime/`: Packet capture and flow feature extraction engine.
- `preprocessing/`: Data cleaning, scaling, and SMOTE balancing.
- `training/`: Model selection and benchmarking pipeline.
- `models/`: Storage for trained models and scalers.

SENTINEL AI is a production-grade, real-time network security suite designed to detect and mitigate botnet traffic using state-of-the-art Machine Learning and Explainable AI (XAI).

## 🚀 Key Features
- **Real-time Neural Defense**: High-speed packet sniffing with Scapy and AI-driven flow analysis.
- **Cosmic-Glass Dashboard**: A premium Streamlit interface with glassmorphism aesthetics and real-time telemetry.
- **Explainable AI (SHAP)**: Deep transparency into model decisions, showing exactly why a flow was flagged.
- **Academic Workflow**: Implements the 10-step CICIDS2017 pipeline (SMOTE, Bayesian Optimization, etc.).
- **Autonomous Simulation**: Full functionality even without administrative network access.

## 🛠️ Quick Start

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Orchestrated Launch (Recommended)
This will start the Backend API, the Sniffer Engine, and the Dashboard in parallel.
```bash
python run_all.py
```

### Docker Compose
Bring up the services in containers (the frontend reads `API_URL` from the environment):
```bash
docker compose up --build
```

See `CHANGELOG.md` for recent internal fixes and added healthchecks for container orchestration.

### Environment
Set the backend API address if it's not on the local host (useful for Docker):

```powershell
setx API_URL "http://localhost:8000"
# or for the current shell only (PowerShell): $env:API_URL = 'http://localhost:8000'
```

The Streamlit frontend reads `API_URL` from the environment and falls back to `http://localhost:8000`.

### 3. Manual Initialization
If you want to train the model from scratch:
```bash
python init_project.py
```

Note: `init_project.py` will save model artifacts to the `models/` directory. If you run `run_all.py` and artifacts are missing, the orchestrator will automatically run `init_project.py` for you.

## 🏗️ System Architecture
- **Backend**: FastAPI with SQLAlchemy/SQLite.
- **Frontend**: Streamlit with Plotly & Custom CSS.
- **Engine**: Scapy for packet ingestion + XGBoost/LightGBM for inference.
- **XAI**: SHAP for feature attribution.

## 🔬 Methodology
SENTINEL follows the academic standards for network intrusion detection:
1. Bidirectional Flow (Biflow) aggregation.
2. Statistical feature extraction (Temporal, Length, Flags).
3. Synthetic balancing via SMOTE.
4. Champion model selection (Random Forest vs GBDT).

## 📝 Documentation
- **API Reference**: Swagger UI available at `http://localhost:8000/docs`
- **Model Info**: Logs and metrics stored in `models/best_model_info.txt`

## ⚠️ Requirements
- Python 3.11+
- Admin/Root privileges (for real-time packet capture)
- Npcap/WinPcap (Windows only, for packet sniffing)

---
**Developed by SENTINEL AI Research Group**
