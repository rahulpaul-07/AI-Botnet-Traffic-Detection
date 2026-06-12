import subprocess
import time
import os
import sys
import requests
from loguru import logger


def wait_for_backend(port: int = 8000, timeout: int = 30) -> bool:
    end_time = time.time() + timeout
    url = f"http://localhost:{port}/health"
    while time.time() < end_time:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                logger.info("Backend API is live.")
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def run_all():
    logger.info("🛡️ SENTINEL AI - Orchestrator Starting...")
    
    # 1. Initialize project if models are missing
    if not os.path.exists("models/best_botnet_model.pkl"):
        logger.info("Model artifacts missing. Running initialization...")
        subprocess.run([sys.executable, "init_project.py"], check=True)
    
    # 2. Start Backend API
    logger.info("Starting Backend API (FastAPI)...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend_api.main:app", "--port", "8000"],
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
    )
    
    if not wait_for_backend():
        logger.error("Backend API failed to start within the expected time.")
        backend_proc.terminate()
        return
    
    # 3. Start Real-time Sniffer
    logger.info("Starting Real-time Network Engine...")
    sniffer_proc = subprocess.Popen(
        [sys.executable, "realtime/sniffer.py"],
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
    )
    
    # 4. Start Streamlit Dashboard
    logger.info("Starting Streamlit Dashboard...")
    frontend_proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend_streamlit/app.py"],
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
    )
    
    logger.success("="*50)
    logger.success("SENTINEL AI SYSTEM FULLY OPERATIONAL")
    logger.info("Dashboard: http://localhost:8501")
    logger.info("API Docs:  http://localhost:8000/docs")
    logger.success("="*50)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.warning("Shutting down SENTINEL services...")
        backend_proc.terminate()
        sniffer_proc.terminate()
        frontend_proc.terminate()
        logger.info("All services stopped.")

if __name__ == "__main__":
    run_all()
