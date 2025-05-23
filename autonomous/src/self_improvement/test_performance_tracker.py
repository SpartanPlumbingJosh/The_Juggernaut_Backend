"""
Test cases for the performance tracking system.
"""

import pytest
import os
import sys
import json
import tempfile
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.self_improvement.performance_tracker import PerformanceTracker

class TestPerformanceTracker:
    """Test suite for the PerformanceTracker class."""
    
    @pytest.fixture
    def temp_metrics_file(self):
        """Create a temporary metrics file for testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            f.write(b'{}')
            return f.name
    
    @pytest.fixture
    def tracker(self, temp_metrics_file):
        """Create a PerformanceTracker instance for testing."""
        return PerformanceTracker(metrics_file=temp_metrics_file)
    
    def test_initialization(self, tracker, temp_metrics_file):
        """Test that the tracker initializes correctly."""
        assert tracker.metrics_file == temp_metrics_file
        assert "user_satisfaction" in tracker.metrics
        assert "learning_efficiency" in tracker.metrics
        assert "knowledge_retention" in tracker.metrics
        assert "task_completion" in tracker.metrics
    
    def test_record_user_satisfaction(self, tracker):
        """Test recording user satisfaction ratings."""
        tracker.record_user_satisfaction(4.5, "Good response")
        assert len(tracker.metrics["user_satisfaction"]) == 1
        assert tracker.metrics["user_satisfaction"][0]["rating"] == 4.5
        assert tracker.metrics["user_satisfaction"][0]["feedback"] == "Good response"
    
    def test_record_learning_efficiency(self, tracker):
        """Test recording learning efficiency metrics."""
        tracker.record_learning_efficiency("task-123", 10.5, 0.85)
        assert len(tracker.metrics["learning_efficiency"]) == 1
        assert tracker.metrics["learning_efficiency"][0]["task_id"] == "task-123"
        assert tracker.metrics["learning_efficiency"][0]["learning_time"] == 10.5
        assert tracker.metrics["learning_efficiency"][0]["improvement_rate"] == 0.85
    
    def test_record_knowledge_retention(self, tracker):
        """Test recording knowledge retention metrics."""
        tracker.record_knowledge_retention("python", 0.92)
        assert len(tracker.metrics["knowledge_retention"]) == 1
        assert tracker.metrics["knowledge_retention"][0]["topic"] == "python"
        assert tracker.metrics["knowledge_retention"][0]["recall_accuracy"] == 0.92
    
    def test_record_task_completion(self, tracker):
        """Test recording task completion metrics."""
        tracker.record_task_completion("task-456", True, 25.3)
        assert len(tracker.metrics["task_completion"]) == 1
        assert tracker.metrics["task_completion"][0]["task_id"] == "task-456"
        assert tracker.metrics["task_completion"][0]["success"] is True
        assert tracker.metrics["task_completion"][0]["completion_time"] == 25.3
    
    def test_get_metrics_summary(self, tracker):
        """Test getting a summary of metrics."""
        # Add some test data
        tracker.record_user_satisfaction(4.0)
        tracker.record_user_satisfaction(5.0)
        tracker.record_learning_efficiency("task-1", 10.0, 0.8)
        tracker.record_learning_efficiency("task-2", 15.0, 0.9)
        tracker.record_knowledge_retention("topic-1", 0.85)
        tracker.record_knowledge_retention("topic-2", 0.95)
        tracker.record_task_completion("task-1", True, 20.0)
        tracker.record_task_completion("task-2", False, 30.0)
        
        summary = tracker.get_metrics_summary()
        
        assert summary["user_satisfaction_avg"] == 4.5
        assert summary["learning_efficiency_avg"] == 0.85
        assert summary["knowledge_retention_avg"] == 0.9
        assert summary["task_completion_rate"] == 0.5
    
    def test_save_and_load_metrics(self, temp_metrics_file):
        """Test that metrics are saved to and loaded from file correctly."""
        # Create a tracker and add some data
        tracker1 = PerformanceTracker(metrics_file=temp_metrics_file)
        tracker1.record_user_satisfaction(4.5)
        
        # Create a new tracker that should load the saved data
        tracker2 = PerformanceTracker(metrics_file=temp_metrics_file)
        
        assert len(tracker2.metrics["user_satisfaction"]) == 1
        assert tracker2.metrics["user_satisfaction"][0]["rating"] == 4.5
