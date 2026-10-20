import re
from typing import Dict, Tuple, List, Optional
import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class MLRiskEstimator:
    """Experimental feature-based ML Command Risk Classifier (scikit-learn RandomForest)"""

    def __init__(self):
        self.sk_available = SKLEARN_AVAILABLE
        self.model = None
        self.labels = ["low", "medium", "high", "critical"]
        if self.sk_available:
            self._train_baseline_model()

    def extract_features(self, command: str, intent_type: str = "command") -> np.ndarray:
        """Extract structured domain features from command text and intent"""
        cmd_lower = command.lower()
        
        is_read_only = 1.0 if any(k in cmd_lower for k in ["dir", "ls", "get-childitem", "get-process", "type", "cat", "echo", "where", "which"]) else 0.0
        is_destructive = 1.0 if any(k in cmd_lower for k in ["del", "rm", "remove-item", "stop-process", "kill", "format", "rd /s", "rmdir"]) else 0.0
        is_system_path = 1.0 if any(k in cmd_lower for k in ["c:\\windows", "system32", "program files", "/etc", "/root"]) else 0.0
        has_wildcard = 1.0 if ("*" in cmd_lower or "?" in cmd_lower) else 0.0
        has_recursive = 1.0 if ("-recurse" in cmd_lower or "/s" in cmd_lower or "-r" in cmd_lower) else 0.0
        requires_admin = 1.0 if any(k in cmd_lower for k in ["netstat", "reg ", "sc ", "runas", "set-executionpolicy"]) else 0.0
        is_install = 1.0 if intent_type == "install" or "pip install" in cmd_lower or "npm install" in cmd_lower else 0.0

        return np.array([[is_read_only, is_destructive, is_system_path, has_wildcard, has_recursive, requires_admin, is_install]])

    def _train_baseline_model(self):
        """Train RandomForest classifier on curated command risk samples"""
        training_samples = [
            ("dir", "low"),
            ("ls -la", "low"),
            ("get-childitem", "low"),
            ("get-process", "low"),
            ("pip install numpy", "medium"),
            ("mkdir backups", "medium"),
            ("copy file.txt D:\\", "medium"),
            ("npm run build", "medium"),
            ("del temp.log", "high"),
            ("rmdir /s /q test_dir", "high"),
            ("remove-item logs\\*.log", "high"),
            ("stop-process -name node -force", "high"),
            ("remove-item -recurse -force C:\\Windows", "critical"),
            ("rd /s /q C:\\", "critical"),
            ("format C:", "critical")
        ]

        X = np.vstack([self.extract_features(cmd) for cmd, label in training_samples])
        y = np.array([self.labels.index(label) for cmd, label in training_samples])

        self.model = RandomForestClassifier(n_estimators=20, random_state=42)
        self.model.fit(X, y)

    def predict_risk(self, command: str, intent_type: str = "command") -> Dict:
        """Predict risk level using ML model with feature breakdown"""
        if not self.sk_available or not self.model:
            return {"risk_level": "low", "confidence": 0.5, "ml_available": False}

        features = self.extract_features(command, intent_type)
        probs = self.model.predict_proba(features)[0]
        pred_idx = np.argmax(probs)
        pred_label = self.labels[pred_idx]
        confidence = float(probs[pred_idx])

        feature_dict = {
            "is_read_only": bool(features[0][0]),
            "is_destructive": bool(features[0][1]),
            "is_system_path": bool(features[0][2]),
            "has_wildcard": bool(features[0][3]),
            "has_recursive": bool(features[0][4]),
            "requires_admin": bool(features[0][5]),
            "is_install": bool(features[0][6]),
        }

        return {
            "risk_level": pred_label,
            "confidence": round(confidence, 2),
            "ml_available": True,
            "model_type": "RandomForestClassifier",
            "features": feature_dict
        }

ml_risk_estimator = MLRiskEstimator()
