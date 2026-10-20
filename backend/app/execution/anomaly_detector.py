import time
from typing import List, Dict, Optional

class BehavioralAnomalyDetector:
    """Monitors command execution patterns for behavioral anomalies and suspicious activity spikes"""

    def __init__(self, window_seconds: int = 300):
        self.window_seconds = window_seconds
        self.events: List[Dict] = []

    def record_event(self, command: str, status: str, exit_code: int, risk_level: str):
        """Record command execution event in rolling window"""
        now = time.time()
        self.events.append({
            "timestamp": now,
            "command": command,
            "status": status,
            "exit_code": exit_code,
            "risk_level": risk_level
        })
        # Prune events outside window
        cutoff = now - self.window_seconds
        self.events = [e for e in self.events if e["timestamp"] >= cutoff]

    def analyze_behavior(self) -> Dict:
        """Calculate anomaly score and return structured alert if suspicious pattern is detected"""
        if not self.events:
            return {"anomaly_detected": False, "score": 0.0, "details": "Normal activity (no recent events)"}

        count = len(self.events)
        failures = sum(1 for e in self.events if e["exit_code"] != 0 or e["status"] == "failed")
        critical_high_count = sum(1 for e in self.events if e["risk_level"] in ["high", "critical"])
        
        failure_rate = failures / count if count > 0 else 0
        high_risk_ratio = critical_high_count / count if count > 0 else 0
        frequency_rate = count / (self.window_seconds / 60)  # commands per minute

        # Anomaly scoring model
        score = 0.0
        reasons = []

        if frequency_rate > 15:
            score += 0.35
            reasons.append(f"Unusually high command frequency ({round(frequency_rate, 1)} cmds/min)")

        if failure_rate > 0.5 and count >= 3:
            score += 0.40
            reasons.append(f"High command failure rate ({int(failure_rate * 100)}% failures in last {count} commands)")

        if high_risk_ratio > 0.4 and count >= 2:
            score += 0.35
            reasons.append(f"Elevated ratio of destructive/high-risk commands ({critical_high_count} high-risk commands)")

        score = min(1.0, score)
        anomaly_detected = score >= 0.6

        return {
            "anomaly_detected": anomaly_detected,
            "score": round(score, 2),
            "reasons": reasons,
            "metrics": {
                "events_in_window": count,
                "failure_rate": round(failure_rate, 2),
                "high_risk_ratio": round(high_risk_ratio, 2),
                "commands_per_min": round(frequency_rate, 1)
            },
            "suggested_action": "Review active session commands and slow down automated execution" if anomaly_detected else "Continue normal execution"
        }

anomaly_detector = BehavioralAnomalyDetector()
