"""
Self-improvement mechanisms for the autonomous system.
"""

from typing import Dict, List, Any, Optional
import json
import datetime

class PerformanceTracker:
    """
    Tracks performance metrics for the autonomous system.
    """
    def __init__(self, metrics_file: str = None):
        self.metrics_file = metrics_file or "/home/ubuntu/autonomous/learning/metrics/performance_data.json"
        self.metrics = {
            "user_satisfaction": [],
            "learning_efficiency": [],
            "knowledge_retention": [],
            "task_completion": []
        }
        self._load_metrics()
    
    def _load_metrics(self):
        """Load metrics from file if it exists."""
        try:
            with open(self.metrics_file, 'r') as f:
                self.metrics = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._save_metrics()
    
    def _save_metrics(self):
        """Save metrics to file."""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def record_user_satisfaction(self, rating: float, feedback: Optional[str] = None):
        """Record user satisfaction rating."""
        self.metrics["user_satisfaction"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "rating": rating,
            "feedback": feedback
        })
        self._save_metrics()
    
    def record_learning_efficiency(self, task_id: str, learning_time: float, improvement_rate: float):
        """Record learning efficiency metrics."""
        self.metrics["learning_efficiency"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "task_id": task_id,
            "learning_time": learning_time,
            "improvement_rate": improvement_rate
        })
        self._save_metrics()
    
    def record_knowledge_retention(self, topic: str, recall_accuracy: float):
        """Record knowledge retention metrics."""
        self.metrics["knowledge_retention"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "topic": topic,
            "recall_accuracy": recall_accuracy
        })
        self._save_metrics()
    
    def record_task_completion(self, task_id: str, success: bool, completion_time: float):
        """Record task completion metrics."""
        self.metrics["task_completion"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "task_id": task_id,
            "success": success,
            "completion_time": completion_time
        })
        self._save_metrics()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        return {
            "user_satisfaction_avg": self._calculate_avg_satisfaction(),
            "learning_efficiency_avg": self._calculate_avg_learning_efficiency(),
            "knowledge_retention_avg": self._calculate_avg_knowledge_retention(),
            "task_completion_rate": self._calculate_task_completion_rate()
        }
    
    def _calculate_avg_satisfaction(self) -> float:
        """Calculate average user satisfaction rating."""
        ratings = [entry["rating"] for entry in self.metrics["user_satisfaction"]]
        return sum(ratings) / len(ratings) if ratings else 0.0
    
    def _calculate_avg_learning_efficiency(self) -> float:
        """Calculate average learning efficiency."""
        rates = [entry["improvement_rate"] for entry in self.metrics["learning_efficiency"]]
        return sum(rates) / len(rates) if rates else 0.0
    
    def _calculate_avg_knowledge_retention(self) -> float:
        """Calculate average knowledge retention."""
        accuracies = [entry["recall_accuracy"] for entry in self.metrics["knowledge_retention"]]
        return sum(accuracies) / len(accuracies) if accuracies else 0.0
    
    def _calculate_task_completion_rate(self) -> float:
        """Calculate task completion success rate."""
        if not self.metrics["task_completion"]:
            return 0.0
        successful_tasks = sum(1 for entry in self.metrics["task_completion"] if entry["success"])
        return successful_tasks / len(self.metrics["task_completion"])
