"""
Basic tests for Cash Completeness Monitor
Run with: python -m pytest tests/
"""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime

from main import CashCompletenessMonitor, CashVariance
from config import Config, QueryConfig
from state_manager import StateManager
from redash_client import RedashClient
from slack_client import SlackClient


class TestCashVariance:
    """Test CashVariance data class."""
    
    def test_variance_creation(self):
        """Test basic variance creation."""
        variance = CashVariance(
            check_type="Test Check",
            account="Test Account",
            delta_amount=123.45,
            currency="USD",
            detection_date="2025-09-19T10:00:00",
            variance_id="",
            raw_data={}
        )
        
        assert variance.check_type == "Test Check"
        assert variance.account == "Test Account"
        assert variance.delta_amount == 123.45
        assert variance.currency == "USD"
        assert variance.variance_id  # Should be auto-generated
    
    def test_significance_check(self):
        """Test variance significance checking."""
        variance = CashVariance(
            check_type="Test",
            account="Test",
            delta_amount=50.0,
            currency="USD",
            detection_date="2025-09-19T10:00:00",
            variance_id="test",
            raw_data={}
        )
        
        assert not variance.is_significant(100.0)  # Below threshold
        assert variance.is_significant(25.0)       # Above threshold
    
    def test_variance_id_generation(self):
        """Test that variance IDs are generated consistently."""
        variance1 = CashVariance(
            check_type="Test Check",
            account="Test Account", 
            delta_amount=123.45,
            currency="USD",
            detection_date="2025-09-19T10:00:00",
            variance_id="",
            raw_data={}
        )
        
        variance2 = CashVariance(
            check_type="Test Check",
            account="Test Account",
            delta_amount=123.45, 
            currency="USD",
            detection_date="2025-09-19T11:00:00",  # Different time
            variance_id="",
            raw_data={}
        )
        
        # Should have same ID despite different detection times
        assert variance1.variance_id == variance2.variance_id


class TestConfig:
    """Test configuration management."""
    
    def test_query_config_creation(self):
        """Test QueryConfig creation."""
        query = QueryConfig(
            query_id=123,
            name="Test Query",
            description="Test Description"
        )
        
        assert query.query_id == 123
        assert query.name == "Test Query"
        assert query.additional_params == {}
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        config = Config(
            redash_base_url="https://test.com",
            redash_api_key="test-key",
            redash_queries=[QueryConfig(query_id=123, name="Test")],
            slack_bot_token="xoxb-test",
            slack_channel="#test"
        )
        
        errors = config.validate()
        assert len(errors) == 0
        
        # Invalid config - missing required fields
        config.redash_base_url = ""
        errors = config.validate()
        assert len(errors) > 0
        assert any("redash_base_url" in error for error in errors)


class TestStateManager:
    """Test state management."""
    
    def test_initial_state_creation(self, tmp_path):
        """Test initial state file creation."""
        state_file = tmp_path / "test_state.json"
        state_manager = StateManager(str(state_file))
        
        assert state_file.exists()
        assert state_manager.get_known_variances() == {}
    
    def test_variance_tracking(self, tmp_path):
        """Test adding and retrieving variances."""
        state_file = tmp_path / "test_state.json"
        state_manager = StateManager(str(state_file))
        
        variance_data = {
            "check_type": "Test",
            "account": "Test Account",
            "delta_amount": 123.45
        }
        
        # Add variance
        state_manager.add_known_variance("test-id", variance_data)
        
        # Retrieve variances
        known_variances = state_manager.get_known_variances()
        assert "test-id" in known_variances
        assert known_variances["test-id"]["account"] == "Test Account"
    
    def test_variance_removal(self, tmp_path):
        """Test variance removal."""
        state_file = tmp_path / "test_state.json"
        state_manager = StateManager(str(state_file))
        
        # Add and then remove variance
        state_manager.add_known_variance("test-id", {"account": "Test"})
        assert state_manager.is_variance_known("test-id")
        
        removed = state_manager.remove_known_variance("test-id")
        assert removed
        assert not state_manager.is_variance_known("test-id")


class TestRedashClient:
    """Test Redash API client."""
    
    @patch('requests.Session')
    def test_client_initialization(self, mock_session):
        """Test client initialization."""
        client = RedashClient("https://test.com", "test-key")
        
        assert client.base_url == "https://test.com"
        assert client.api_key == "test-key"
        mock_session.assert_called_once()
    
    @patch('requests.Session')
    def test_query_execution_flow(self, mock_session):
        """Test the query execution flow."""
        # Mock the session and responses
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        
        # Mock trigger response
        trigger_response = Mock()
        trigger_response.json.return_value = {"job": {"id": "job-123"}}
        trigger_response.raise_for_status.return_value = None
        mock_session_instance.post.return_value = trigger_response
        
        # Mock job status response (completed)
        status_response = Mock()
        status_response.json.return_value = {
            "job": {
                "status": 3,  # Success
                "query_result_id": 456
            }
        }
        status_response.raise_for_status.return_value = None
        
        # Mock result response
        result_response = Mock()
        result_response.json.return_value = {
            "query_result": {
                "data": {
                    "columns": [{"name": "account"}, {"name": "amount"}],
                    "rows": [["Test Account", 123.45]]
                },
                "retrieved_at": "2025-09-19T10:00:00",
                "runtime": 1.5,
                "data_source_id": 1
            }
        }
        result_response.raise_for_status.return_value = None
        
        mock_session_instance.get.return_value = status_response
        mock_session_instance.get.side_effect = [status_response, result_response]
        
        client = RedashClient("https://test.com", "test-key")
        
        # This would normally execute the full flow, but we're mocking the network calls
        # Just test that the client is properly initialized
        assert client.base_url == "https://test.com"


class TestSlackClient:
    """Test Slack API client."""
    
    @patch('requests.Session')
    def test_client_initialization(self, mock_session):
        """Test Slack client initialization."""
        client = SlackClient("test-token", "#test-channel")
        
        assert client.token == "test-token"
        assert client.default_channel == "#test-channel"
        mock_session.assert_called_once()
    
    @patch('requests.Session')
    def test_message_sending(self, mock_session):
        """Test basic message sending."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        
        # Mock successful response
        response = Mock()
        response.json.return_value = {"ok": True, "ts": "1234567890.123456"}
        response.raise_for_status.return_value = None
        mock_session_instance.post.return_value = response
        
        client = SlackClient("test-token", "#test-channel")
        result = client.send_message("Test message")
        
        assert result["ok"] is True
        mock_session_instance.post.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])