"""
Configuration Management for Cash Completeness Monitor
Handles loading and validation of system configuration.
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class QueryConfig:
    """Configuration for a single Redash query."""
    query_id: int
    name: str
    description: str = ""
    additional_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}


@dataclass
class Config:
    """Main configuration class for the monitoring system."""
    
    # Redash configuration
    redash_base_url: str
    redash_api_key: str
    redash_queries: List[QueryConfig]
    
    # Slack configuration
    slack_bot_token: str
    slack_channel: str
    
    # System configuration
    significance_threshold: float = 100.0
    state_storage_path: str = "state.json"
    log_level: str = "INFO"
    query_timeout: int = 300
    
    # Alert configuration
    alert_on_system_errors: bool = True
    daily_status_report: bool = False
    status_report_time: str = "08:00"
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'Config':
        """
        Load configuration from a JSON file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Config instance
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.error(f"Configuration file not found: {config_path}")
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Convert query configurations
            queries = []
            for query_data in config_data.get('redash_queries', []):
                queries.append(QueryConfig(**query_data))
            
            # Create config instance
            config = cls(
                redash_base_url=config_data['redash_base_url'],
                redash_api_key=config_data['redash_api_key'],
                redash_queries=queries,
                slack_bot_token=config_data['slack_bot_token'],
                slack_channel=config_data['slack_channel'],
                significance_threshold=config_data.get('significance_threshold', 100.0),
                state_storage_path=config_data.get('state_storage_path', 'state.json'),
                log_level=config_data.get('log_level', 'INFO'),
                query_timeout=config_data.get('query_timeout', 300),
                alert_on_system_errors=config_data.get('alert_on_system_errors', True),
                daily_status_report=config_data.get('daily_status_report', False),
                status_report_time=config_data.get('status_report_time', '08:00')
            )
            
            logger.info(f"Configuration loaded successfully from {config_path}")
            return config
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            raise ValueError(f"Invalid configuration file: {str(e)}")
    
    @classmethod
    def load_from_env(cls) -> 'Config':
        """
        Load configuration from environment variables.
        
        Returns:
            Config instance
        """
        try:
            # Parse queries from environment (JSON string)
            queries_json = os.getenv('REDASH_QUERIES', '[]')
            queries_data = json.loads(queries_json)
            queries = [QueryConfig(**q) for q in queries_data]
            
            config = cls(
                redash_base_url=os.environ['REDASH_BASE_URL'],
                redash_api_key=os.environ['REDASH_API_KEY'],
                redash_queries=queries,
                slack_bot_token=os.environ['SLACK_BOT_TOKEN'],
                slack_channel=os.environ['SLACK_CHANNEL'],
                significance_threshold=float(os.getenv('SIGNIFICANCE_THRESHOLD', '100.0')),
                state_storage_path=os.getenv('STATE_STORAGE_PATH', 'state.json'),
                log_level=os.getenv('LOG_LEVEL', 'INFO'),
                query_timeout=int(os.getenv('QUERY_TIMEOUT', '300')),
                alert_on_system_errors=os.getenv('ALERT_ON_SYSTEM_ERRORS', 'true').lower() == 'true',
                daily_status_report=os.getenv('DAILY_STATUS_REPORT', 'false').lower() == 'true',
                status_report_time=os.getenv('STATUS_REPORT_TIME', '08:00')
            )
            
            logger.info("Configuration loaded from environment variables")
            return config
            
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load configuration from environment: {str(e)}")
            raise ValueError(f"Invalid environment configuration: {str(e)}")
    
    def save_to_file(self, config_path: str):
        """
        Save configuration to a JSON file.
        
        Args:
            config_path: Path to save the configuration to
        """
        try:
            config_file = Path(config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dictionary
            config_dict = asdict(self)
            
            # Convert QueryConfig objects to dictionaries
            config_dict['redash_queries'] = [asdict(q) for q in self.redash_queries]
            
            with open(config_file, 'w') as f:
                json.dump(config_dict, f, indent=2, sort_keys=True)
            
            logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
            raise
    
    def validate(self) -> List[str]:
        """
        Validate the configuration and return any errors.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Required fields validation
        if not self.redash_base_url:
            errors.append("redash_base_url is required")
        
        if not self.redash_api_key:
            errors.append("redash_api_key is required")
        
        if not self.slack_bot_token:
            errors.append("slack_bot_token is required")
        
        if not self.slack_channel:
            errors.append("slack_channel is required")
        
        # Queries validation
        if not self.redash_queries:
            errors.append("At least one Redash query must be configured")
        
        for i, query in enumerate(self.redash_queries):
            if not query.query_id:
                errors.append(f"Query {i}: query_id is required")
            if not query.name:
                errors.append(f"Query {i}: name is required")
        
        # Value validation
        if self.significance_threshold < 0:
            errors.append("significance_threshold must be non-negative")
        
        if self.query_timeout <= 0:
            errors.append("query_timeout must be positive")
        
        # URL validation
        if self.redash_base_url and not (
            self.redash_base_url.startswith('http://') or 
            self.redash_base_url.startswith('https://')
        ):
            errors.append("redash_base_url must start with http:// or https://")
        
        return errors
    
    def get_query_by_name(self, name: str) -> Optional[QueryConfig]:
        """Get a query configuration by name."""
        for query in self.redash_queries:
            if query.name == name:
                return query
        return None
    
    def get_query_by_id(self, query_id: int) -> Optional[QueryConfig]:
        """Get a query configuration by ID."""
        for query in self.redash_queries:
            if query.query_id == query_id:
                return query
        return None


def create_sample_config(config_path: str = "config.json"):
    """
    Create a sample configuration file.
    
    Args:
        config_path: Path to create the sample configuration at
    """
    sample_queries = [
        QueryConfig(
            query_id=123,
            name="BAI2 Bank Balance Check",
            description="Compares BAI2 reported balances with internal records",
            additional_params={"account_type": "operations"}
        ),
        QueryConfig(
            query_id=124,
            name="Chase Recovery Variance Check",
            description="Monitors known Chase recovery variances",
            additional_params={"exclude_known": True}
        )
    ]
    
    sample_config = Config(
        redash_base_url="https://your-redash-instance.com",
        redash_api_key="your-redash-api-key-here",
        redash_queries=sample_queries,
        slack_bot_token="xoxb-your-slack-bot-token-here",
        slack_channel="#monthly-reconciliations",
        significance_threshold=100.0,
        state_storage_path="state.json",
        log_level="INFO",
        query_timeout=300,
        alert_on_system_errors=True,
        daily_status_report=False,
        status_report_time="08:00"
    )
    
    sample_config.save_to_file(config_path)
    logger.info(f"Sample configuration created at {config_path}")


if __name__ == "__main__":
    # Create sample configuration if run directly
    create_sample_config()