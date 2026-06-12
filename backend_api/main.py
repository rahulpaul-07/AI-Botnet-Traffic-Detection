from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
from typing import List
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger
import shap


def load_model_files():
    global model, scaler
    model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None
    scaler = joblib.load(SCALER_PATH) if os.path.exists(SCALER_PATH) else None
    logger.info(f"Model loaded: {model is not None}, Scaler loaded: {scaler is not None}")


# --- Database Setup ---

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./botnet_system.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ThreatRecord(Base):
    __tablename__ = "threats"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    src_ip = Column(String)
    dst_port = Column(Integer)
    protocol = Column(String)
    confidence = Column(Float)
    threat_type = Column(String)
    features = Column(JSON)
    status = Column(String, default="Mitigated")

Base.metadata.create_all(bind=engine)

# --- FastAPI App ---
app = FastAPI(
    title="SENTINEL AI - Botnet Detection API", 
    version="5.0",
    description="Advanced AI-powered network security API for real-time botnet detection."
)

@app.on_event("startup")
async def startup_event():
    logger.info("SENTINEL API starting up...")
    db = SessionLocal()
    try:
        count = db.query(ThreatRecord).count()
        if count == 0:
            logger.info("Database is empty. Seeding initial data...")
            await seed_data()
    except Exception as e:
        logger.error(f"Startup seeding failed: {e}")
    finally:
        db.close()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Model Loading ---
MODEL_PATH = "models/best_botnet_model.pkl"
SCALER_PATH = "models/scaler.pkl"

model = None
scaler = None
load_model_files()

class FlowFeatures(BaseModel):
    flow_duration: float
    fwd_packets_tot: int
    bwd_packets_tot: int
    flow_byts_s: float
    flow_pkts_s: float
    pkt_len_mean: float
    pkt_len_std: float
    iat_mean: float
    iat_std: float
    syn_flag_cnt: int
    ack_flag_cnt: int
    psh_flag_cnt: int

class ThreatLogRequest(BaseModel):
    src_ip: str
    dst_port: int
    protocol: str
    confidence: float
    threat_type: str
    features: dict

@app.post("/predict")
async def predict_flow(features: FlowFeatures):
    if not model or not scaler:
        raise HTTPException(status_code=503, detail="Models not initialized. Run init_project.py first.")
    
    try:
        df = pd.DataFrame([features.dict()])
        X_scaled = scaler.transform(df)
        prediction = model.predict(X_scaled)[0]
        
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(X_scaled)[0]
            confidence = float(probabilities[int(prediction)])
        else:
            confidence = 1.0 if int(prediction) == 1 else 0.0
        
        return {
            "is_botnet": bool(prediction),
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/log_threat")
async def log_threat(request: ThreatLogRequest):
    db = SessionLocal()
    try:
        new_threat = ThreatRecord(
            src_ip=request.src_ip,
            dst_port=request.dst_port,
            protocol=request.protocol,
            confidence=request.confidence,
            threat_type=request.threat_type,
            features=request.features
        )
        db.add(new_threat)
        db.commit()
        db.refresh(new_threat)
        logger.warning(f"New threat logged: {request.threat_type} from {request.src_ip}")
        return {"status": "success", "id": new_threat.id}
    finally:
        db.close()

@app.get("/threats", response_model=List[dict])
async def get_threats(limit: int = 50):
    db = SessionLocal()
    try:
        threats = db.query(ThreatRecord).order_by(ThreatRecord.timestamp.desc()).limit(limit).all()
        return [
            {
                "id": t.id,
                "timestamp": t.timestamp,
                "src_ip": t.src_ip,
                "dst_port": t.dst_port,
                "protocol": t.protocol,
                "confidence": t.confidence,
                "threat_type": t.threat_type,
                "status": t.status,
                "features": t.features
            } for t in threats
        ]
    finally:
        db.close()

@app.get("/explain/{threat_id}")
async def explain_threat(threat_id: int):
    db = SessionLocal()
    try:
        threat = db.query(ThreatRecord).filter(ThreatRecord.id == threat_id).first()
        if not threat:
            raise HTTPException(status_code=404, detail="Threat not found")
        
        if not model or not scaler:
            raise HTTPException(status_code=503, detail="Models not initialized")

        try:
            # Reconstruct full feature set in correct order
            feature_order = [
                'flow_duration', 'fwd_packets_tot', 'bwd_packets_tot', 'flow_byts_s',
                'flow_pkts_s', 'pkt_len_mean', 'pkt_len_std', 'iat_mean', 'iat_std',
                'syn_flag_cnt', 'ack_flag_cnt', 'psh_flag_cnt'
            ]
            
            ordered_features = {}
            for feat in feature_order:
                ordered_features[feat] = threat.features.get(feat, 0.0)
            
            df = pd.DataFrame([ordered_features])
            X_scaled = scaler.transform(df)
            
            # Use KernelExplainer for non-tree models if TreeExplainer fails
            try:
                if "XGB" in str(type(model)) or "LGBM" in str(type(model)) or "Forest" in str(type(model)):
                    explainer = shap.TreeExplainer(model)
                    shap_values = explainer.shap_values(X_scaled)
                else:
                    # Fallback to KernelExplainer for generic models
                    # Use a small sample of training data if possible, or just the current sample
                    explainer = shap.KernelExplainer(model.predict_proba, X_scaled)
                    shap_values = explainer.shap_values(X_scaled)
            except Exception as e:
                logger.debug(f"Primary explainer failed, trying generic Explainer: {e}")
                explainer = shap.Explainer(model, X_scaled)
                shap_values = explainer(X_scaled).values

            # SHAP return formats vary by model and version
            if hasattr(shap_values, "values"): # Handle Explanation object (shap >= 0.40)
                val_arr = shap_values.values
            else:
                val_arr = shap_values

            if isinstance(val_arr, list):
                # Random Forest usually returns a list of arrays [negative_class, positive_class]
                if len(val_arr) > 1:
                    val = val_arr[1][0].tolist()
                else:
                    val = val_arr[0][0].tolist()
            elif isinstance(val_arr, np.ndarray):
                if len(val_arr.shape) == 3: # (batch, features, classes)
                    val = val_arr[0, :, 1].tolist()
                elif len(val_arr.shape) == 2: # (batch, features) or (batch, classes)
                    # If it's (1, features), use it directly
                    # If it's (1, 2) for binary, we need feature values, which should be in the other case
                    val = val_arr[0].tolist()
                else:
                    val = val_arr.tolist()
            else:
                val = list(val_arr)

            # Handle base value (expected value)
            try:
                base_val = explainer.expected_value
                if isinstance(base_val, (list, np.ndarray)):
                    base_val = base_val[1] if len(base_val) > 1 else base_val[0]
            except:
                base_val = 0.5 # Default fallback

            return {
                "base_value": float(base_val),
                "values": val,
                "feature_names": feature_order,
                "actual_features": threat.features
            }
        except Exception as e:
            logger.error(f"SHAP Error: {e}")
            raise HTTPException(status_code=500, detail=f"Explanation engine error: {str(e)}")
    finally:
        db.close()

@app.post("/reload_model")
async def reload_model():
    try:
        load_model_files()
        if not model or not scaler:
            raise HTTPException(status_code=500, detail="Model or scaler failed to load.")
        return {"status": "success", "model_loaded": True, "scaler_loaded": True}
    except Exception as e:
        logger.error(f"Model reload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/seed")
async def seed_data():
    db = SessionLocal()
    try:
        # Clear existing threats (optional, but good for fresh start)
        db.query(ThreatRecord).delete()
        
        threat_types = ["Botnet (DDoS)", "Botnet (C2)", "Botnet (Scanning)", "Botnet (Spam)"]
        protocols = ["TCP", "UDP", "ICMP"]
        
        for i in range(20):
            timestamp = datetime.utcnow() - timedelta(minutes=i*15)
            new_threat = ThreatRecord(
                timestamp=timestamp,
                src_ip=f"10.0.{np.random.randint(1,255)}.{np.random.randint(1,255)}",
                dst_port=int(np.random.choice([80, 443, 22, 3389, 4444, 8080])),
                protocol=str(np.random.choice(protocols)),
                confidence=float(np.random.uniform(0.75, 0.99)),
                threat_type=str(np.random.choice(threat_types)),
                features={
                    "flow_duration": 1000.0, "fwd_packets_tot": 5, "bwd_packets_tot": 5,
                    "flow_byts_s": 500.0, "flow_pkts_s": 10.0, "pkt_len_mean": 64.0,
                    "pkt_len_std": 5.0, "iat_mean": 100.0, "iat_std": 10.0,
                    "syn_flag_cnt": 0, "ack_flag_cnt": 1, "psh_flag_cnt": 0
                }
            )
            db.add(new_threat)
        
        db.commit()
        return {"status": "success", "message": "Seeded 20 threat records."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/health")
async def health():
    return {
        "status": "online", 
        "model_loaded": model is not None,
        "scaler_loaded": scaler is not None,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
