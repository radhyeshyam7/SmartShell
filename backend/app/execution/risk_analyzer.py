import os
import re
from typing import Tuple, Dict
from backend.app.config import settings
from backend.app.execution.ml_risk_estimator import ml_risk_estimator

RISK_LEVEL_ORDER = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4
}

class RiskAnalyzer:
    """Independent deterministic safety classifier with ML-assisted risk estimation fallback & stricter policy enforcement"""
    
    CRITICAL_PATTERNS = [
        re.compile(r'(?i)\b(format|mkfs|diskpart|reg delete)\b'),
        re.compile(r'(?i)\brm\s+-[rRfF]*\s+([/\\]|\*|c:[/\\])'),
        re.compile(r'(?i)\bdel\s+/[fFsSqQ]*\s+c:[/\\](windows|program files)'),
        re.compile(r'(?i)>[>\s]*[/\\]dev[/\\](sda|hda|null)'),
        re.compile(r'(?i):()\{:|:\};:'),  # Fork bomb
    ]
    
    HIGH_PATTERNS = [
        re.compile(r'(?i)\b(rmdir|rd)\s+/[sSqQ]'),
        re.compile(r'(?i)\bremove-item\s+.*-recurse'),
        re.compile(r'(?i)\b(taskkill|stop-process|killall|pkill)\b'),
        re.compile(r'(?i)\b(chmod|chown|icacls|takeown)\b'),
        re.compile(r'(?i)\b(drop\s+database|delete\s+from)\b'),
        re.compile(r'(?i)\b(del|remove-item)\b'),
    ]
    
    MEDIUM_PATTERNS = [
        re.compile(r'(?i)\b(pip|npm|npx|cargo|go)\s+(install|add|update|remove|uninstall)\b'),
        re.compile(r'(?i)\bpython\s+-m\s+(venv|pip)\b'),
        re.compile(r'(?i)\b(mkdir|md|new-item|touch)\b'),
        re.compile(r'(?i)\b(type\s+nul\s*>|echo\s+.*>)\b'),
        re.compile(r'(?i)\b(git\s+(commit|push|checkout|reset|rebase|merge))\b'),
        re.compile(r'(?i)\b(move|copy|copy-item|move-item)\b'),
    ]
    
    UNSAFE_PATH_PREFIXES = [
        'c:\\windows', 'c:\\program files', 'c:\\program files (x86)',
        '/etc', '/sys', '/boot', '/root', '/proc'
    ]

    def analyze_command(self, command: str, working_dir: str = ".") -> Tuple[str, bool, str]:
        """
        Returns (risk_level, requires_approval, reason)
        Evaluates deterministic rules + ML risk estimator, enforcing the stricter safety policy.
        """
        cmd_lower = command.strip().lower()
        det_risk = "low"
        reason = "Standard query requiring routine review."

        # Check Critical
        for pat in self.CRITICAL_PATTERNS:
            if pat.search(cmd_lower):
                det_risk = "critical"
                reason = "Destructive operation detected that can harm system integrity."
                break
                
        if det_risk == "low":
            for prefix in self.UNSAFE_PATH_PREFIXES:
                if prefix in cmd_lower:
                    det_risk = "critical"
                    reason = f"Operation targets protected system location '{prefix}'."
                    break

        if det_risk == "low":
            for pat in self.HIGH_PATTERNS:
                if pat.search(cmd_lower):
                    det_risk = "high"
                    reason = "Recursive deletion, process termination, or permission modification."
                    break

        if det_risk == "low":
            for pat in self.MEDIUM_PATTERNS:
                if pat.search(cmd_lower):
                    det_risk = "medium"
                    reason = "Software installation, environment creation, or filesystem modification."
                    break

        if det_risk == "low":
            base_cmd = cmd_lower.split()[0] if cmd_lower.split() else ""
            if base_cmd in settings.SAFE_COMMANDS and not any(op in cmd_lower for op in ['>', '>>', '|', '&', ';']):
                det_risk = "low"
                reason = "Read-only bounded query or standard utility command."

        # ML Risk Estimator Evaluation
        final_risk = det_risk
        try:
            ml_eval = ml_risk_estimator.predict_risk(command)
            ml_risk = ml_eval.get("risk_level", "low")
            # Stricter policy enforcement
            if RISK_LEVEL_ORDER.get(ml_risk, 1) > RISK_LEVEL_ORDER.get(det_risk, 1):
                final_risk = ml_risk
                reason += f" (ML Risk Classifier elevated risk rating to {ml_risk.upper()})"
        except Exception:
            pass

        requires_approval = final_risk in ["medium", "high", "critical"] or (settings.AUTO_APPROVE_LOW_RISK is False and final_risk == "low")
        return final_risk, requires_approval, reason

risk_analyzer = RiskAnalyzer()
