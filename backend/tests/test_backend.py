import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.execution.risk_analyzer import risk_analyzer
from backend.app.utils.sanitization import sanitize_text
from backend.app.execution.executor import executor

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "SmartShell" in data["app_name"]

def test_risk_analyzer():
    # Low Risk
    risk, req_app, _ = risk_analyzer.analyze_command("dir")
    assert risk == "low"

    # Medium Risk
    risk, req_app, _ = risk_analyzer.analyze_command("pip install numpy")
    assert risk == "medium"
    assert req_app is True

    # High Risk
    risk, req_app, _ = risk_analyzer.analyze_command("rmdir /s /q test_dir")
    assert risk == "high"
    assert req_app is True

    # Critical Risk
    risk, req_app, _ = risk_analyzer.analyze_command("format c:")
    assert risk == "critical"
    assert req_app is True

def test_secret_sanitization():
    fake_key = "AIzaSy" + "FakeApiKeyTestStringForSanitiz123"
    raw_text = f"Connecting with key {fake_key}"
    clean = sanitize_text(raw_text)
    assert "AIzaSy" not in clean or "[REDACTED" in clean

import sys

def test_command_executor():
    code, stdout, stderr, duration = executor.execute_command(f'"{sys.executable}" --version')
    assert code == 0
    assert "Python" in stdout or "Python" in stderr
