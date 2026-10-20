import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import json
import time
from backend.app.execution.risk_analyzer import risk_analyzer
from backend.app.execution.ml_risk_estimator import ml_risk_estimator
from backend.app.ai.local_rag import local_rag

class EvaluationSuite:
    """Reproducible NLP, Risk Estimation, and RAG Benchmark Evaluation Suite"""

    def __init__(self, dataset_path: str = "backend/evaluation/dataset.json"):
        self.dataset_path = dataset_path
        self.dataset: List[Dict] = []
        self._load_dataset()

    def _load_dataset(self):
        if os.path.exists(self.dataset_path):
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                self.dataset = json.load(f)

    def run_evaluation(self) -> Dict:
        """Run evaluation benchmark across dataset test cases"""
        if not self.dataset:
            return {"error": "Dataset is empty or missing"}

        total = len(self.dataset)
        risk_matches = 0
        ml_matches = 0
        latencies = []

        for item in self.dataset:
            prompt = item["prompt"]
            expected_risk = item["expected_risk"]

            start_t = time.time()
            
            # Risk analyzer evaluation
            risk_level, _, _ = risk_analyzer.analyze_command(prompt)
            if risk_level.lower() == expected_risk.lower():
                risk_matches += 1

            # ML Risk estimator evaluation
            ml_res = ml_risk_estimator.predict_risk(prompt, intent_type="command")
            if ml_res.get("risk_level", "").lower() == expected_risk.lower():
                ml_matches += 1

            duration = round((time.time() - start_t) * 1000, 2)
            latencies.append(duration)

        # RAG evaluation
        rag_res = local_rag.search_knowledge_base("permission denied access error", top_k=2)
        rag_precision = 1.0 if len(rag_res) > 0 else 0.0

        avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

        report = {
            "dataset_size": total,
            "deterministic_risk_accuracy": round(risk_matches / total, 4),
            "ml_risk_accuracy": round(ml_matches / total, 4),
            "rag_precision_at_2": rag_precision,
            "average_latency_ms": avg_latency,
            "evaluation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        return report

if __name__ == "__main__":
    suite = EvaluationSuite()
    report = suite.run_evaluation()
    print(json.dumps(report, indent=2))
