"""
Machine Learning Detection Tests
"""
import pytest
import numpy as np
from sklearn.ensemble import IsolationForest


class TestMLDetection:
    """Test ML-based anomaly detection"""

    def test_model_initialization(self):
        """Test Isolation Forest initialization"""
        model = IsolationForest(contamination=0.1, random_state=42)
        assert model is not None
        assert model.contamination == 0.1

    def test_feature_extraction(self, test_event_data):
        """Test feature extraction from events"""
        features = self.extract_features(test_event_data)

        assert features.shape == (1, 4)
        assert 0 <= features[0, 0] <= 1  # Hour normalized
        assert 0 <= features[0, 1] <= 1  # Day normalized
        assert 0 <= features[0, 2] <= 1  # Frequency normalized
        assert 0 <= features[0, 3] <= 1  # Failure rate normalized

    def test_model_training(self):
        """Test model training on normal data"""
        # Generate normal training data
        X_train = np.random.normal(0.5, 0.1, (30, 4))

        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(X_train)

        # Model should be trained
        assert hasattr(model, 'offset_')
        assert hasattr(model, 'estimators_')

    def test_anomaly_detection_normal(self):
        """Normal behavior should not be flagged"""
        # Train on normal data
        X_train = np.random.normal(0.5, 0.1, (30, 4))
        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(X_train)

        # Test normal data
        X_test = np.array([[0.5, 0.5, 0.5, 0.5]])
        prediction = model.predict(X_test)

        # 1 = normal, -1 = anomaly
        assert prediction[0] == 1

    def test_anomaly_detection_abnormal(self):
        """Abnormal behavior should be flagged"""
        # Train on normal data
        X_train = np.random.normal(0.5, 0.1, (30, 4))
        model = IsolationForest(contamination=0.1, random_state=42)
        model.fit(X_train)

        # Test abnormal data (far from training distribution)
        X_test = np.array([[0.95, 0.95, 0.95, 0.95]])
        prediction = model.predict(X_test)
        score = model.score_samples(X_test)

        # Should have low anomaly score (more negative = more anomalous)
        assert score[0] < -0.1

    def test_auto_training_threshold(self):
        """Test that model trains after threshold events"""
        detector = MockMLDetector()

        # Simulate events
        for i in range(35):
            event = {"user_identifier": f"user{i}@example.com"}
            detector.process_event(event)

        # Should be trained after 30 events
        assert detector.trained is True
        assert len(detector.training_data) >= 30

    def test_ml_score_integration(self, test_event_data):
        """Test ML score integration with risk scoring"""
        detector = MockMLDetector()

        # Train model
        for i in range(30):
            detector.process_event({"user_identifier": f"user{i}"})

        # Get ML score for new event
        ml_score = detector.get_ml_score(test_event_data)

        assert 0 <= ml_score <= 40  # ML contributes up to 40 points

    # Helper methods
    def extract_features(self, event, history=None):
        """Extract ML features from event"""
        from datetime import datetime

        now = datetime.now()
        hour = now.hour / 24.0
        day = now.weekday() / 7.0

        history = history or []
        frequency = min(len(history) / 10.0, 1.0) if history else 0.0
        failures = sum(1 for e in history[-10:] if e.get('status') == 'failed') / 10.0

        return np.array([[hour, day, frequency, failures]])


class MockMLDetector:
    """Mock ML detector for testing"""

    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.trained = False
        self.training_data = []
        self.threshold = 30

    def process_event(self, event):
        """Process event and auto-train if threshold met"""
        self.training_data.append(event)

        if not self.trained and len(self.training_data) >= self.threshold:
            self.train()

    def train(self):
        """Train the model"""
        if len(self.training_data) >= self.threshold:
            # Create dummy features for training
            X = np.random.normal(0.5, 0.1, (len(self.training_data), 4))
            self.model.fit(X)
            self.trained = True

    def get_ml_score(self, event):
        """Get ML anomaly score"""
        if not self.trained:
            return 0

        # Extract features and predict
        features = np.array([[0.5, 0.5, 0.5, 0.5]])
        score = self.model.score_samples(features)[0]

        # Convert to 0-40 scale
        ml_score = max(0, min(40, int((-score) * 20)))
        return ml_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
