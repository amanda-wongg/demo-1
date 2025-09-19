#!/usr/bin/env python3
"""
Real-Time Customer Cash Completeness Check Automation
Author: AI Assistant
Date: September 19, 2025

This system automates the Customer Cash Completeness Check process,
transforming it from a manual weekly task to an automated daily monitoring
system with intelligent variance detection and management-by-exception alerting.
"""

import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from redash_client import RedashClient
from slack_client import SlackClient
from state_manager import StateManager
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CashVariance:
    """Represents a cash variance detected in the system."""
    check_type: str
    account: str
    delta_amount: float
    currency: str
    detection_date: str
    variance_id: str
    raw_data: Dict[str, Any]
    
    def __post_init__(self):
        """Generate a unique ID for this variance if not provided."""
        if not self.variance_id:
            self.variance_id = self._generate_variance_id()
    
    def _generate_variance_id(self) -> str:
        """Generate a unique identifier for this variance."""
        # Create a hash based on key variance characteristics
        variance_key = f"{self.check_type}_{self.account}_{self.delta_amount}_{self.currency}"
        return hashlib.md5(variance_key.encode()).hexdigest()[:12]
    
    def is_significant(self, threshold: float = 100.0) -> bool:
        """Check if variance exceeds significance threshold."""
        return abs(self.delta_amount) >= threshold


class CashCompletenessMonitor:
    """Main monitoring agent for cash completeness checks."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the monitoring agent."""
        self.config = Config.load_from_file(config_path)
        self.redash_client = RedashClient(
            base_url=self.config.redash_base_url,
            api_key=self.config.redash_api_key
        )
        self.slack_client = SlackClient(
            token=self.config.slack_bot_token,
            channel=self.config.slack_channel
        )
        self.state_manager = StateManager(self.config.state_storage_path)
        
        logger.info("Cash Completeness Monitor initialized")
    
    def run_daily_check(self) -> Dict[str, Any]:
        """Execute the daily cash completeness check."""
        logger.info("Starting daily cash completeness check")
        
        try:
            # Calculate time window for check
            end_time = datetime.now()
            start_time = end_time - timedelta(days=1)
            
            logger.info(f"Checking period: {start_time.isoformat()} to {end_time.isoformat()}")
            
            # Execute queries and collect results
            query_results = self._execute_queries(start_time, end_time)
            
            # Analyze results for variances
            detected_variances = self._analyze_query_results(query_results)
            
            # Filter out known variances
            new_variances = self._filter_new_variances(detected_variances)
            
            # Process alerts for new variances
            alerts_sent = self._process_alerts(new_variances)
            
            # Update state with new variances
            self._update_state(new_variances)
            
            # Prepare summary
            summary = {
                "timestamp": datetime.now().isoformat(),
                "period_checked": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "total_variances_detected": len(detected_variances),
                "new_variances_found": len(new_variances),
                "alerts_sent": alerts_sent,
                "status": "success"
            }
            
            logger.info(f"Daily check completed successfully: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Daily check failed: {str(e)}", exc_info=True)
            self._send_error_alert(str(e))
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    def _execute_queries(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Execute all configured Redash queries for the given time period."""
        logger.info("Executing Redash queries")
        
        query_results = {}
        
        for query_config in self.config.redash_queries:
            query_id = query_config["query_id"]
            query_name = query_config["name"]
            
            try:
                logger.info(f"Executing query: {query_name} (ID: {query_id})")
                
                # Prepare query parameters
                parameters = {
                    "start_date": start_time.strftime("%Y-%m-%d"),
                    "end_date": end_time.strftime("%Y-%m-%d"),
                    **query_config.get("additional_params", {})
                }
                
                # Execute query
                result = self.redash_client.execute_query(query_id, parameters)
                query_results[query_name] = result
                
                logger.info(f"Query {query_name} executed successfully, {len(result.get('rows', []))} rows returned")
                
            except Exception as e:
                logger.error(f"Failed to execute query {query_name}: {str(e)}")
                query_results[query_name] = {"error": str(e)}
        
        return query_results
    
    def _analyze_query_results(self, query_results: Dict[str, Any]) -> List[CashVariance]:
        """Analyze query results to detect cash variances."""
        logger.info("Analyzing query results for variances")
        
        detected_variances = []
        
        for query_name, result in query_results.items():
            if "error" in result:
                logger.warning(f"Skipping analysis for {query_name} due to query error")
                continue
            
            try:
                variances = self._parse_query_for_variances(query_name, result)
                detected_variances.extend(variances)
                
                logger.info(f"Found {len(variances)} variances in {query_name}")
                
            except Exception as e:
                logger.error(f"Failed to analyze results for {query_name}: {str(e)}")
        
        return detected_variances
    
    def _parse_query_for_variances(self, query_name: str, result: Dict[str, Any]) -> List[CashVariance]:
        """Parse individual query result to extract variances."""
        variances = []
        rows = result.get("rows", [])
        columns = result.get("columns", [])
        
        # Create column name to index mapping
        col_map = {col["name"]: idx for idx, col in enumerate(columns)}
        
        for row in rows:
            try:
                # Extract variance data based on expected column structure
                # This assumes standard columns: account, delta_amount, currency, etc.
                variance = CashVariance(
                    check_type=query_name,
                    account=row[col_map.get("account", 0)] if "account" in col_map else "Unknown",
                    delta_amount=float(row[col_map.get("delta_amount", 1)] or 0),
                    currency=row[col_map.get("currency", 2)] if "currency" in col_map else "USD",
                    detection_date=datetime.now().isoformat(),
                    variance_id="",  # Will be auto-generated
                    raw_data={"row": row, "columns": columns}
                )
                
                # Only include significant variances
                if variance.is_significant(self.config.significance_threshold):
                    variances.append(variance)
                    
            except (IndexError, ValueError, TypeError) as e:
                logger.warning(f"Failed to parse row in {query_name}: {str(e)}")
        
        return variances
    
    def _filter_new_variances(self, detected_variances: List[CashVariance]) -> List[CashVariance]:
        """Filter out variances that have already been reported."""
        logger.info(f"Filtering {len(detected_variances)} detected variances for new ones")
        
        known_variances = self.state_manager.get_known_variances()
        new_variances = []
        
        for variance in detected_variances:
            if variance.variance_id not in known_variances:
                new_variances.append(variance)
                logger.info(f"New variance detected: {variance.account} - ${variance.delta_amount}")
            else:
                logger.debug(f"Known variance skipped: {variance.variance_id}")
        
        logger.info(f"Found {len(new_variances)} new variances")
        return new_variances
    
    def _process_alerts(self, new_variances: List[CashVariance]) -> int:
        """Send alerts for new variances."""
        if not new_variances:
            logger.info("No new variances to alert on - maintaining silence (management by exception)")
            return 0
        
        alerts_sent = 0
        
        for variance in new_variances:
            try:
                self._send_variance_alert(variance)
                alerts_sent += 1
                logger.info(f"Alert sent for variance: {variance.variance_id}")
                
            except Exception as e:
                logger.error(f"Failed to send alert for variance {variance.variance_id}: {str(e)}")
        
        return alerts_sent
    
    def _send_variance_alert(self, variance: CashVariance):
        """Send a Slack alert for a specific variance."""
        # Format the alert message
        message = self._format_variance_alert(variance)
        
        # Send to Slack
        self.slack_client.send_message(message)
    
    def _format_variance_alert(self, variance: CashVariance) -> str:
        """Format a variance into a Slack alert message."""
        emoji = "⚠️" if abs(variance.delta_amount) > 10000 else "🔍"
        
        message = f"""
{emoji} **New Cash Variance Detected**: {datetime.now().strftime('%b %d, %Y')} 🤖

A new, unexpected variance was detected in the last 24 hours.

**Check**: {variance.check_type}
**Account**: {variance.account}
**Delta**: {variance.currency} {variance.delta_amount:,.2f}
**Variance ID**: `{variance.variance_id}`

**Action Required**: Investigation needed. <@channel>

_This is an automated alert from the Cash Completeness Monitor. Only new variances are reported._
        """.strip()
        
        return message
    
    def _send_error_alert(self, error_message: str):
        """Send an error alert to Slack."""
        message = f"""
🚨 **Cash Completeness Monitor Error**

The automated cash completeness check encountered an error:

```
{error_message}
```

**Action Required**: Please check the monitoring system. <@channel>

_Timestamp_: {datetime.now().isoformat()}
        """.strip()
        
        try:
            self.slack_client.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send error alert: {str(e)}")
    
    def _update_state(self, new_variances: List[CashVariance]):
        """Update the state manager with new variances."""
        for variance in new_variances:
            self.state_manager.add_known_variance(variance.variance_id, asdict(variance))
        
        logger.info(f"State updated with {len(new_variances)} new variances")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        known_variances = self.state_manager.get_known_variances()
        
        return {
            "system_status": "operational",
            "last_check": self.state_manager.get_last_check_time(),
            "known_variances_count": len(known_variances),
            "config_loaded": bool(self.config),
            "timestamp": datetime.now().isoformat()
        }


def main():
    """Main entry point for the monitoring agent."""
    logger.info("Starting Cash Completeness Monitor")
    
    try:
        # Initialize monitor
        monitor = CashCompletenessMonitor()
        
        # Run daily check
        result = monitor.run_daily_check()
        
        # Log result
        if result["status"] == "success":
            logger.info("Daily check completed successfully")
        else:
            logger.error("Daily check failed")
        
        return result
        
    except Exception as e:
        logger.error(f"Monitor failed to start: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    main()