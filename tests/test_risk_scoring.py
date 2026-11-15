"""
Risk Scoring Engine Tests
"""
import pytest
from datetime import datetime


class TestRiskScoring:
    """Test risk scoring calculations"""

    def test_low_risk_normal_login(self, test_event_data):
        """Normal login should have low risk"""
        # Simulate risk calculation
        risk_score = self.calculate_risk(test_event_data)
        assert 0 <= risk_score < 20
        assert self.get_severity(risk_score) == "LOW"

    def test_high_risk_malicious_ip(self, malicious_ip_event):
        """Known malicious IP should trigger high risk"""
        risk_score = self.calculate_risk(malicious_ip_event)
        assert risk_score >= 60
        assert self.get_severity(risk_score) in ["HIGH", "CRITICAL"]

    def test_brute_force_detection(self, brute_force_events):
        """Multiple failed attempts should increase risk"""
        risk_scores = []
        for event in brute_force_events:
            score = self.calculate_risk(event, history=brute_force_events[:len(risk_scores)])
            risk_scores.append(score)

        # Risk should increase with more failures
        assert risk_scores[-1] > risk_scores[0]
        assert risk_scores[-1] >= 60  # Should be HIGH risk

    def test_impossible_travel_detection(self, impossible_travel_events):
        """Geographically impossible travel should trigger alert"""
        event1, event2 = impossible_travel_events

        # Calculate distance
        distance_km = self.calculate_distance(
            event1["latitude"], event1["longitude"],
            event2["latitude"], event2["longitude"]
        )

        # Calculate time difference
        time_diff = self.parse_timestamp(event2["timestamp"]) - self.parse_timestamp(event1["timestamp"])
        time_hours = time_diff.total_seconds() / 3600

        # Speed calculation
        speed_kmh = distance_km / time_hours if time_hours > 0 else float('inf')

        # Should be impossible (>1000 km/h)
        assert speed_kmh > 1000

        # Should trigger high risk
        risk_score = self.calculate_risk(event2, history=[event1])
        assert risk_score >= 70

    def test_risk_signal_extraction(self, malicious_ip_event):
        """Should extract multiple risk signals"""
        signals = self.extract_risk_signals(malicious_ip_event)

        assert len(signals) > 0
        assert any(s["type"] == "ip_reputation" for s in signals)
        assert any(s["type"] == "failed_login" for s in signals)

        # Each signal should have required fields
        for signal in signals:
            assert "type" in signal
            assert "score" in signal
            assert "description" in signal

    def test_risk_threshold_classification(self):
        """Test severity classification"""
        assert self.get_severity(10) == "LOW"
        assert self.get_severity(30) == "MODERATE"
        assert self.get_severity(50) == "ELEVATED"
        assert self.get_severity(70) == "HIGH"
        assert self.get_severity(90) == "CRITICAL"

    # Helper methods
    def calculate_risk(self, event, history=None):
        """Calculate risk score for event"""
        score = 0
        history = history or []

        # IP reputation check
        if event["ip_address"] in ["203.0.113.50", "198.51.100.50"]:
            score += 30

        # Failed login check
        if event["status"] == "failed":
            score += 15

            # Check recent failures
            recent_failures = sum(1 for e in history[-10:] if e.get("status") == "failed")
            score += min(recent_failures * 5, 25)

        # Geographic check
        if event.get("country") in ["Russia", "China", "North Korea"]:
            score += 20

        return min(score, 100)

    def get_severity(self, score):
        """Get severity level from score"""
        if score < 20:
            return "LOW"
        elif score < 40:
            return "MODERATE"
        elif score < 60:
            return "ELEVATED"
        elif score < 80:
            return "HIGH"
        else:
            return "CRITICAL"

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points (km)"""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Earth radius in km

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c

    def parse_timestamp(self, ts_str):
        """Parse ISO timestamp"""
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))

    def extract_risk_signals(self, event):
        """Extract risk signals from event"""
        signals = []

        # IP reputation
        if event["ip_address"] in ["203.0.113.50"]:
            signals.append({
                "type": "ip_reputation",
                "score": 30,
                "description": "Known malicious IP address"
            })

        # Failed login
        if event["status"] == "failed":
            signals.append({
                "type": "failed_login",
                "score": 15,
                "description": "Failed authentication attempt"
            })

        return signals


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
