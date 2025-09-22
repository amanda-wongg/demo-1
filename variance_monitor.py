#!/usr/bin/env python3
"""
Variance Monitor - Automated Bank Account Variance Checker
Runs every Monday to check for variances from first of month to yesterday
Sends Slack alerts when variance column is not zero
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/variance_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class VarianceRecord:
    """Data class for variance records"""
    bank_account: str
    reconciled_payment_records: float
    bt_date_1: str
    bt_balance_1: float
    bt_date_2: str
    bt_balance_2: float
    movement: float
    difference: float
    unreconciled_bt_credit: float
    unreconciled_bt_debit: float
    unreconciled_bt_absolute_total: float
    variance: float

class VarianceMonitor:
    """Main class for monitoring bank account variances"""
    
    def __init__(self):
        self.db_connection_string = os.getenv('DATABASE_CONNECTION_STRING')
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.slack_channel = os.getenv('SLACK_CHANNEL', '#finance-alerts')
        self.engine = None
        
    def validate_config(self) -> bool:
        """Validate that all required configuration is present"""
        if not self.db_connection_string:
            logger.error("DATABASE_CONNECTION_STRING environment variable not set")
            return False
            
        if not self.slack_webhook_url:
            logger.error("SLACK_WEBHOOK_URL environment variable not set")
            return False
            
        return True
    
    def connect_to_database(self) -> bool:
        """Establish database connection"""
        try:
            self.engine = create_engine(self.db_connection_string)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def get_date_range(self) -> tuple:
        """Get the date range from first of month to yesterday"""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        first_of_month = today.replace(day=1)
        
        logger.info(f"Date range: {first_of_month} to {yesterday}")
        return first_of_month, yesterday
    
    def execute_variance_query(self, start_date: datetime.date, end_date: datetime.date) -> List[VarianceRecord]:
        """
        Execute the variance query for the given date range
        
        Note: You'll need to replace this query with your actual SQL query
        This is a template based on the data structure you provided
        """
        query = """
        SELECT 
            bank_account,
            reconciled_payment_records,
            bt_date_1,
            bt_balance_1,
            bt_date_2,
            bt_balance_2,
            movement,
            difference,
            unreconciled_bt_credit,
            unreconciled_bt_debit,
            unreconciled_bt_absolute_total,
            variance
        FROM payment_records_movement_and_bank_balances_by_account
        WHERE bt_date_1 >= :start_date 
        AND bt_date_2 <= :end_date
        AND variance != 0
        ORDER BY bank_account
        """
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(query), 
                    {"start_date": start_date, "end_date": end_date}
                )
                
                records = []
                for row in result:
                    records.append(VarianceRecord(
                        bank_account=row.bank_account,
                        reconciled_payment_records=float(row.reconciled_payment_records or 0),
                        bt_date_1=str(row.bt_date_1),
                        bt_balance_1=float(row.bt_balance_1 or 0),
                        bt_date_2=str(row.bt_date_2),
                        bt_balance_2=float(row.bt_balance_2 or 0),
                        movement=float(row.movement or 0),
                        difference=float(row.difference or 0),
                        unreconciled_bt_credit=float(row.unreconciled_bt_credit or 0),
                        unreconciled_bt_debit=float(row.unreconciled_bt_debit or 0),
                        unreconciled_bt_absolute_total=float(row.unreconciled_bt_absolute_total or 0),
                        variance=float(row.variance or 0)
                    ))
                
                logger.info(f"Found {len(records)} records with non-zero variance")
                return records
                
        except Exception as e:
            logger.error(f"Failed to execute variance query: {e}")
            raise
    
    def format_variance_message(self, records: List[VarianceRecord], start_date: datetime.date, end_date: datetime.date) -> Dict[str, Any]:
        """Format the variance records into a Slack message"""
        if not records:
            return {
                "text": f"✅ *Variance Check Complete* - {start_date} to {end_date}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"✅ *No variances detected* for period {start_date} to {end_date}\n\nAll bank account reconciliations are balanced."
                        }
                    }
                ]
            }
        
        # Create summary
        total_variance = sum(abs(record.variance) for record in records)
        affected_accounts = len(set(record.bank_account for record in records))
        
        # Create detailed blocks
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🚨 *VARIANCE ALERT* - {start_date} to {end_date}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n• {len(records)} variance records found\n• {affected_accounts} accounts affected\n• Total absolute variance: ${total_variance:,.2f}"
                }
            },
            {
                "type": "divider"
            }
        ]
        
        # Add details for each variance (limit to first 10 to avoid message size limits)
        for i, record in enumerate(records[:10]):
            variance_emoji = "🔴" if record.variance < 0 else "🟡"
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{variance_emoji} *{record.bank_account}*\n"
                            f"• Variance: ${record.variance:,.2f}\n"
                            f"• Movement: ${record.movement:,.2f}\n"
                            f"• Difference: ${record.difference:,.2f}\n"
                            f"• Period: {record.bt_date_1} to {record.bt_date_2}"
                }
            })
        
        if len(records) > 10:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"... and {len(records) - 10} more variance records. Check the full report for details."
                }
            })
        
        return {
            "text": f"🚨 VARIANCE ALERT: {len(records)} variances detected ({start_date} to {end_date})",
            "blocks": blocks
        }
    
    def send_slack_notification(self, message: Dict[str, Any]) -> bool:
        """Send notification to Slack"""
        try:
            # Add channel to message if specified
            if self.slack_channel:
                message["channel"] = self.slack_channel
            
            response = requests.post(
                self.slack_webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("Slack notification sent successfully")
                return True
            else:
                logger.error(f"Failed to send Slack notification: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False
    
    def run_variance_check(self) -> bool:
        """Main method to run the complete variance check"""
        logger.info("Starting variance check...")
        
        try:
            # Validate configuration
            if not self.validate_config():
                return False
            
            # Connect to database
            if not self.connect_to_database():
                return False
            
            # Get date range
            start_date, end_date = self.get_date_range()
            
            # Execute query
            variance_records = self.execute_variance_query(start_date, end_date)
            
            # Format and send notification
            message = self.format_variance_message(variance_records, start_date, end_date)
            
            if not self.send_slack_notification(message):
                logger.error("Failed to send Slack notification")
                return False
            
            # Log summary
            if variance_records:
                logger.warning(f"Variance check completed: {len(variance_records)} variances found")
            else:
                logger.info("Variance check completed: No variances found")
            
            return True
            
        except Exception as e:
            logger.error(f"Variance check failed: {e}")
            # Send error notification to Slack
            error_message = {
                "text": f"❌ Variance Check Failed",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"❌ *Variance Check Failed*\n\nError: {str(e)}\n\nPlease check the logs and fix the issue."
                        }
                    }
                ]
            }
            self.send_slack_notification(error_message)
            return False

def main():
    """Main entry point"""
    monitor = VarianceMonitor()
    success = monitor.run_variance_check()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()