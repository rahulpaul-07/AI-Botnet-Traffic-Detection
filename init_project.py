import os
import time
import requests
from loguru import logger
from preprocessing.pipeline import DataPipeline
from training.trainer import ModelTrainer

def initialize_project():
    logger.info("🛡️ SENTINEL AI - System Initialization Started")
    
    # Ensure directories exist
    directories = ["data", "models", "models/plots", "logs"]
    for d in directories:
        os.makedirs(d, exist_ok=True)
        logger.info(f"Directory verified: {d}")

    # 1. Preprocessing
    logger.info("Step 1: Running Data Pipeline (Synthetic Generation + SMOTE)...")
    try:
        pipeline = DataPipeline()
        df = pipeline.load_data()
        X, y = pipeline.preprocess(df)
        X_train, X_test, y_train, y_test = pipeline.balance_and_split(X, y)
        
        # Save processed data
        import numpy as np
        np.save("data/X_train.npy", X_train)
        np.save("data/X_test.npy", X_test)
        np.save("data/y_train.npy", y_train)
        np.save("data/y_test.npy", y_test)
        logger.success("Preprocessing Pipeline Complete.")
    except Exception as e:
        logger.error(f"Preprocessing Failed: {e}")
        return

    # 2. Training
    logger.info("Step 2: Training Champion Models (XGBoost/LightGBM)...")
    try:
        trainer = ModelTrainer()
        X_train, X_test, y_train, y_test = trainer.load_data()
        best_model = trainer.train_and_evaluate(X_train, X_test, y_train, y_test)
        logger.success(f"Training Complete! Champion Model: {best_model}")
    except Exception as e:
        logger.error(f"Training Failed: {e}")
        return

    # 3. Environment Warm-up
    logger.info("Step 3: System Warm-up and Seeding...")
    logger.info("NOTE: If the API is not running, seeding will be skipped. Run 'uvicorn backend_api.main:app' and use the UI sync button.")
    
    try:
        # Try to seed if backend is up
        response = requests.post("http://localhost:8000/seed", timeout=2)
        if response.status_code == 200:
            logger.success("Database seeded with initial threat data.")
    except:
        logger.warning("Backend API not reachable for seeding. Skipping initial seed.")

    logger.info("="*50)
    logger.success("SENTINEL AI READY FOR OPERATION")
    logger.info("Run 'uvicorn backend_api.main:app' to start backend")
    logger.info("Run 'streamlit run frontend_streamlit/app.py' to start dashboard")
    logger.info("="*50)

if __name__ == "__main__":
    initialize_project()
