import os
import time
import pandas as pd
import numpy as np
from scapy.all import sniff, IP, TCP, UDP
from collections import defaultdict
import joblib
from loguru import logger
import threading
import requests
import random

class RealTimeEngine:
    def __init__(self, model_path="models/best_botnet_model.pkl", scaler_path="models/scaler.pkl"):
        self.model = joblib.load(model_path) if os.path.exists(model_path) else None
        self.scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None
        self.flows = defaultdict(lambda: {
            'start_time': time.time(),
            'pkt_count': 0,
            'byte_count': 0,
            'fwd_packets': 0,
            'bwd_packets': 0,
            'packet_lengths': [],
            'flags': {'SYN': 0, 'ACK': 0, 'PSH': 0}
        })
        self.active = False
        self.api_url = "http://localhost:8000"

    def packet_callback(self, pkt):
        """Processes a single captured packet."""
        try:
            if IP in pkt:
                ip_src = pkt[IP].src
                ip_dst = pkt[IP].dst
                proto = pkt[IP].proto
                sport = pkt.sport if (TCP in pkt or UDP in pkt) else 0
                dport = pkt.dport if (TCP in pkt or UDP in pkt) else 0
                
                # Create a unique flow ID
                flow_id = tuple(sorted([(ip_src, sport), (ip_dst, dport)])) + (proto,)
                
                flow = self.flows[flow_id]
                flow['pkt_count'] += 1
                flow['byte_count'] += len(pkt)
                flow['packet_lengths'].append(len(pkt))
                
                if TCP in pkt:
                    flags = pkt[TCP].flags
                    if 'S' in flags: flow['flags']['SYN'] += 1
                    if 'A' in flags: flow['flags']['ACK'] += 1
                    if 'P' in flags: flow['flags']['PSH'] += 1
                
                # Check if flow should be exported (every 10 packets)
                if flow['pkt_count'] >= 10:
                    self._analyze_flow(flow_id, flow)
                    del self.flows[flow_id]
        except Exception as e:
            # Silently handle malformed packets in real-time
            pass

    def _analyze_flow(self, flow_id, flow_data):
        """Extracts features and sends to ML model for prediction."""
        duration = time.time() - flow_data['start_time']
        if duration <= 0: duration = 0.0001
        
        features = {
            'flow_duration': float(duration * 1000000),
            'fwd_packets_tot': int(flow_data['pkt_count'] // 2 + 1),
            'bwd_packets_tot': int(flow_data['pkt_count'] // 2),
            'flow_byts_s': float(flow_data['byte_count'] / duration),
            'flow_pkts_s': float(flow_data['pkt_count'] / duration),
            'pkt_len_mean': float(np.mean(flow_data['packet_lengths'])),
            'pkt_len_std': float(np.std(flow_data['packet_lengths']) if len(flow_data['packet_lengths']) > 1 else 0),
            'iat_mean': float((duration / flow_data['pkt_count']) * 1000 if flow_data['pkt_count'] > 0 else 0),
            'iat_std': 0.0,
            'syn_flag_cnt': int(flow_data['flags']['SYN']),
            'ack_flag_cnt': int(flow_data['flags']['ACK']),
            'psh_flag_cnt': int(flow_data['flags']['PSH'])
        }
        
        df = pd.DataFrame([features])
        
        if self.model and self.scaler:
            X_scaled = self.scaler.transform(df)
            prediction = self.model.predict(X_scaled)[0]
            confidence = self.model.predict_proba(X_scaled)[0].max()
            
            if prediction == 1:
                logger.warning(f"🚨 BOTNET DETECTED: {flow_id[0][0]} -> {flow_id[1][0]} | Confidence: {confidence:.2%}")
                self._report_threat(flow_id, features, confidence)

    def _report_threat(self, flow_id, features, confidence):
        """Sends threat data to the backend API."""
        try:
            payload = {
                "src_ip": str(flow_id[0][0]),
                "dst_port": int(flow_id[1][1]),
                "protocol": "TCP" if flow_id[2] == 6 else "UDP",
                "confidence": float(confidence),
                "threat_type": "Botnet (Real-time Detection)",
                "features": features
            }
            requests.post(f"{self.api_url}/log_threat", json=payload, timeout=1)
        except Exception as e:
            logger.error(f"Failed to report threat to API: {e}")

    def start_sniffing(self, interface=None):
        """Starts real-time packet capture with a simulation fallback."""
        self.active = True
        
        def run_sniff():
            try:
                logger.info(f"Initiating Scapy Sniffer on {interface if interface else 'default'}...")
                sniff(iface=interface, prn=self.packet_callback, store=0, stop_filter=lambda x: not self.active)
            except Exception as e:
                logger.error(f"LIVE CAPTURE ERROR: {e}")
                logger.warning("⚠️ CRITICAL: Administrative privileges or Npcap/WinPcap missing.")
                logger.warning("🔄 SWITCHING TO AUTONOMOUS SIMULATION MODE...")
                self.run_simulation()

        sniff_thread = threading.Thread(target=run_sniff, daemon=True)
        sniff_thread.start()

    def run_simulation(self):
        """Generates high-fidelity simulated traffic flows for demonstration."""
        logger.info("🚀 SENTINEL Simulation Engine Active.")
        
        attack_types = [
            ("Mirai Variant", 4444, "TCP", 50, {'SYN': 40, 'ACK': 10, 'PSH': 5}),
            ("C2 Beacon", 8080, "TCP", 5, {'SYN': 1, 'ACK': 4, 'PSH': 2}),
            ("UDP Flood", 53, "UDP", 200, {'SYN': 0, 'ACK': 0, 'PSH': 0}),
            ("SSH Brute Force", 22, "TCP", 30, {'SYN': 15, 'ACK': 15, 'PSH': 10})
        ]

        while self.active:
            # Randomly decide if malicious or benign
            is_malicious = np.random.random() > 0.80
            
            if is_malicious:
                name, port, proto_str, pkts, flags = random.choice(attack_types)
                src_ip = f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
                dst_port = port
                proto = 6 if proto_str == "TCP" else 17
                
                mock_flow_data = {
                    'start_time': time.time() - random.uniform(0.5, 5),
                    'pkt_count': pkts,
                    'byte_count': pkts * random.randint(64, 1500),
                    'packet_lengths': [random.randint(64, 1500)] * pkts,
                    'flags': flags
                }
                logger.info(f"Injecting simulated attack: {name} from {src_ip}")
            else:
                # Benign traffic
                src_ip = f"192.168.1.{random.randint(2, 254)}"
                dst_port = random.choice([80, 443, 53, 123])
                proto = 6 if dst_port != 53 and dst_port != 123 else 17
                pkts = random.randint(5, 20)
                
                mock_flow_data = {
                    'start_time': time.time() - random.uniform(1, 10),
                    'pkt_count': pkts,
                    'byte_count': pkts * random.randint(100, 1000),
                    'packet_lengths': [random.randint(100, 1000)] * pkts,
                    'flags': {'SYN': 1, 'ACK': pkts-1, 'PSH': random.randint(0, 5)}
                }
            
            mock_flow_id = ((src_ip, random.randint(1024, 65535)), ("10.0.0.1", dst_port), proto)
            
            try:
                self._analyze_flow(mock_flow_id, mock_flow_data)
            except Exception as e:
                logger.error(f"Analysis error in simulation: {e}")
            
            time.sleep(random.uniform(1, 3))

    def stop(self):
        self.active = False
        logger.info("🛑 SENTINEL Real-time Engine Shutdown.")


if __name__ == "__main__":
    engine = RealTimeEngine()
    engine.start_sniffing()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        engine.stop()
