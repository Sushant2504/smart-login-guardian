"""
ML Anomaly Detection using Isolation Forest
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime
from typing import Dict, List, Any
import json


class MLAnomalyDetector:
    """Machine Learning Anomaly Detector using Isolation Forest"""

    def __init__(self, contamination: float = 0.1, n_estimators: int = 100):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=n_estimators,
            max_samples=256
        )
        self.trained = False
        self.feature_buffer: List[np.ndarray] = []
        self.training_threshold = 30
        self.total_processed = 0
        self.anomalies_detected = 0
        self.feature_names = ["hour_of_day", "day_of_week", "login_frequency", "failure_rate"]

    def extract_features(self, event_data: Dict, user_history: List[Dict]) -> np.ndarray:
        """
        Extract 4D feature vector from event data

        Features:
        1. Hour of day (0-1): Temporal pattern
        2. Day of week (0-1): Weekly behavior
        3. Login frequency (0-1): Access cadence
        4. Failure rate (0-1): Recent failures
        """
        # Feature 1: Hour of day (normalized 0-1)
        now = datetime.now()
        hour_of_day = now.hour / 24.0

        # Feature 2: Day of week (normalized 0-1)
        day_of_week = now.weekday() / 7.0

        # Feature 3: Login frequency (capped at 10, normalized 0-1)
        login_freq = min(len(user_history) / 10.0, 1.0) if user_history else 0.0

        # Feature 4: Failure rate in last 10 events (0-1)
        if user_history:
            recent = user_history[-10:]
            failures = sum(1 for e in recent if e.get('status') == 'failed')
            failure_rate = failures / len(recent) if recent else 0.0
        else:
            failure_rate = 0.0

        return np.array([hour_of_day, day_of_week, login_freq, failure_rate])

    def predict(self, event_data: Dict, user_history: List[Dict]) -> Dict[str, Any]:
        """
        Predict if event is anomalous

        Returns:
            Dictionary with:
            - anomaly: bool
            - score: int (0-100)
            - status: str ('training' or 'active')
            - features: list of feature values
        """
        features = self.extract_features(event_data, user_history)
        self.total_processed += 1

        # Training phase
        if not self.trained:
            self.feature_buffer.append(features)
            if len(self.feature_buffer) >= self.training_threshold:
                # Train model
                X = np.array(self.feature_buffer)
                self.model.fit(X)
                self.trained = True

            return {
                "anomaly": False,
                "score": 0,
                "status": "training",
                "progress": len(self.feature_buffer) / self.training_threshold * 100,
                "features": features.tolist(),
                "feature_names": self.feature_names
            }

        # Prediction phase
        features_2d = features.reshape(1, -1)
        prediction = self.model.predict(features_2d)[0]
        anomaly_score_raw = self.model.score_samples(features_2d)[0]

        # Convert to 0-100 scale (more negative = more anomalous)
        anomaly_score = max(0, min(100, int((-anomaly_score_raw) * 20)))

        is_anomaly = prediction == -1
        if is_anomaly:
            self.anomalies_detected += 1

        return {
            "anomaly": bool(is_anomaly),
            "score": anomaly_score,
            "status": "active",
            "progress": 100,
            "features": features.tolist(),
            "feature_names": self.feature_names,
            "anomaly_score_raw": float(anomaly_score_raw)
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get model statistics"""
        return {
            "trained": self.trained,
            "total_processed": self.total_processed,
            "anomalies_detected": self.anomalies_detected,
            "training_progress": len(self.feature_buffer) / self.training_threshold * 100 if not self.trained else 100,
            "events_in_buffer": len(self.feature_buffer),
            "status": "active" if self.trained else "training"
        }

# Global ML detector instance
ml_detector = MLAnomalyDetector(contamination=0.1, n_estimators=100)
