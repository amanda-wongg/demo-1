#!/usr/bin/env python3
"""
Variance Alert System with Historical Exclusions

This system processes variance data and filters out known historical variances
before sending alerts to Redash/Slack. It provides multiple approaches to handle
approved historical variances.
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
import sqlite3
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VarianceType(Enum):
    EXPECTED = "expected"
    UNEXPECTED = "unexpected"
    APPROVED_HISTORICAL = "approved_historical"

@dataclass
class VarianceRecord:
    """Represents a variance record with metadata"""
    date: datetime
    amount: float
    description: str
    category: str
    variance_type: VarianceType = VarianceType.UNEXPECTED
    approval_date: Optional[datetime] = None
    approved_by: Optional[str] = None

class HistoricalVarianceManager:
    """Manages historical variance exclusions and approvals"""
    
    def __init__(self, db_path: str = "variance_history.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database for storing historical variances"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_variances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                category TEXT,
                variance_type TEXT,
                approval_date TEXT,
                approved_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS variance_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT UNIQUE NOT NULL,
                category TEXT,
                amount_threshold REAL,
                date_pattern TEXT,
                description_pattern TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_historical_variance(self, variance: VarianceRecord) -> bool:
        """Add a historical variance to the exclusion list"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO historical_variances 
                (date, amount, description, category, variance_type, approval_date, approved_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                variance.date.isoformat(),
                variance.amount,
                variance.description,
                variance.category,
                variance.variance_type.value,
                variance.approval_date.isoformat() if variance.approval_date else None,
                variance.approved_by
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Added historical variance: {variance.description} - ${variance.amount}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding historical variance: {e}")
            return False
    
    def is_historical_variance(self, variance: VarianceRecord, tolerance: float = 0.01) -> bool:
        """Check if a variance matches a known historical variance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check for exact or similar matches
        cursor.execute('''
            SELECT * FROM historical_variances 
            WHERE category = ? 
            AND ABS(amount - ?) <= ?
            AND variance_type IN ('expected', 'approved_historical')
        ''', (variance.category, variance.amount, tolerance * abs(variance.amount)))
        
        results = cursor.fetchall()
        conn.close()
        
        return len(results) > 0
    
    def add_variance_pattern(self, pattern_name: str, category: str = None, 
                           amount_threshold: float = None, description_pattern: str = None) -> bool:
        """Add a pattern for automatically identifying expected variances"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO variance_patterns 
                (pattern_name, category, amount_threshold, description_pattern)
                VALUES (?, ?, ?, ?)
            ''', (pattern_name, category, amount_threshold, description_pattern))
            
            conn.commit()
            conn.close()
            logger.info(f"Added variance pattern: {pattern_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding variance pattern: {e}")
            return False

class VarianceProcessor:
    """Processes variances and determines if they should trigger alerts"""
    
    def __init__(self, historical_manager: HistoricalVarianceManager):
        self.historical_manager = historical_manager
        self.base_threshold = 0.0  # Redash threshold (can be $0.00)
    
    def process_variance(self, variance: VarianceRecord) -> Tuple[bool, str]:
        """
        Process a variance and determine if it should trigger an alert
        
        Returns:
            Tuple[bool, str]: (should_alert, reason)
        """
        # Check if this is a known historical variance
        if self.historical_manager.is_historical_variance(variance):
            return False, f"Known historical variance: {variance.description}"
        
        # Check if variance meets base threshold
        if abs(variance.amount) <= self.base_threshold:
            return False, f"Below threshold: ${variance.amount}"
        
        # Check for pattern matches
        if self._matches_expected_pattern(variance):
            return False, f"Matches expected pattern: {variance.category}"
        
        # If we get here, it's an unexpected variance that should trigger an alert
        return True, f"Unexpected variance detected: ${variance.amount}"
    
    def _matches_expected_pattern(self, variance: VarianceRecord) -> bool:
        """Check if variance matches any expected patterns"""
        conn = sqlite3.connect(self.historical_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM variance_patterns 
            WHERE is_active = TRUE
            AND (category IS NULL OR category = ?)
        ''', (variance.category,))
        
        patterns = cursor.fetchall()
        conn.close()
        
        for pattern in patterns:
            _, _, category, amount_threshold, _, description_pattern, _ = pattern[:7]
            
            # Check amount threshold
            if amount_threshold and abs(variance.amount) <= amount_threshold:
                return True
            
            # Check description pattern
            if description_pattern and description_pattern.lower() in variance.description.lower():
                return True
        
        return False

class RedashIntegration:
    """Handles integration with Redash and Slack notifications"""
    
    def __init__(self, redash_url: str, api_key: str, slack_webhook_url: str = None):
        self.redash_url = redash_url
        self.api_key = api_key
        self.slack_webhook_url = slack_webhook_url
    
    def create_filtered_query(self, base_query: str, exclusions: List[Dict]) -> str:
        """
        Create a Redash query that excludes historical variances
        
        Args:
            base_query: Your original variance query
            exclusions: List of variance exclusion criteria
        """
        # Build exclusion conditions
        exclusion_conditions = []
        
        for exclusion in exclusions:
            condition_parts = []
            
            if 'category' in exclusion:
                condition_parts.append(f"category != '{exclusion['category']}'")
            
            if 'amount_range' in exclusion:
                min_amt, max_amt = exclusion['amount_range']
                condition_parts.append(f"(variance_amount < {min_amt} OR variance_amount > {max_amt})")
            
            if 'description_pattern' in exclusion:
                condition_parts.append(f"description NOT LIKE '%{exclusion['description_pattern']}%'")
            
            if condition_parts:
                exclusion_conditions.append(f"({' AND '.join(condition_parts)})")
        
        # Modify the base query to include exclusions
        if exclusion_conditions:
            where_clause = f"WHERE {' AND '.join(exclusion_conditions)}"
            
            # Insert WHERE clause or add to existing WHERE
            if "WHERE" in base_query.upper():
                filtered_query = base_query.replace("WHERE", f"WHERE ({' AND '.join(exclusion_conditions)}) AND")
            else:
                # Add WHERE clause before ORDER BY, LIMIT, etc.
                for keyword in ["ORDER BY", "GROUP BY", "LIMIT"]:
                    if keyword in base_query.upper():
                        parts = base_query.upper().split(keyword)
                        filtered_query = parts[0] + f" {where_clause} " + keyword + keyword.join(parts[1:])
                        break
                else:
                    filtered_query = base_query + f" {where_clause}"
        else:
            filtered_query = base_query
        
        return filtered_query
    
    def send_slack_alert(self, variance: VarianceRecord, additional_info: str = "") -> bool:
        """Send alert to Slack channel"""
        if not self.slack_webhook_url:
            logger.warning("No Slack webhook URL configured")
            return False
        
        try:
            message = {
                "text": f"🚨 Variance Alert",
                "attachments": [
                    {
                        "color": "danger" if abs(variance.amount) > 1000 else "warning",
                        "fields": [
                            {
                                "title": "Amount",
                                "value": f"${variance.amount:,.2f}",
                                "short": True
                            },
                            {
                                "title": "Category", 
                                "value": variance.category,
                                "short": True
                            },
                            {
                                "title": "Date",
                                "value": variance.date.strftime("%Y-%m-%d"),
                                "short": True
                            },
                            {
                                "title": "Description",
                                "value": variance.description,
                                "short": False
                            }
                        ]
                    }
                ]
            }
            
            if additional_info:
                message["attachments"][0]["fields"].append({
                    "title": "Additional Info",
                    "value": additional_info,
                    "short": False
                })
            
            response = requests.post(self.slack_webhook_url, json=message)
            response.raise_for_status()
            
            logger.info(f"Sent Slack alert for variance: ${variance.amount}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            return False

class VarianceAlertSystem:
    """Main system that orchestrates variance processing and alerting"""
    
    def __init__(self, db_path: str = "variance_history.db", 
                 redash_url: str = None, redash_api_key: str = None,
                 slack_webhook_url: str = None):
        self.historical_manager = HistoricalVarianceManager(db_path)
        self.processor = VarianceProcessor(self.historical_manager)
        self.redash = RedashIntegration(redash_url, redash_api_key, slack_webhook_url) if redash_url else None
    
    def process_variance_data(self, variance_data: List[Dict]) -> List[VarianceRecord]:
        """
        Process a batch of variance data and return only those that should trigger alerts
        
        Args:
            variance_data: List of variance dictionaries with keys: date, amount, description, category
        """
        alerts_to_send = []
        
        for data in variance_data:
            variance = VarianceRecord(
                date=datetime.fromisoformat(data['date']) if isinstance(data['date'], str) else data['date'],
                amount=float(data['amount']),
                description=data.get('description', ''),
                category=data.get('category', 'unknown')
            )
            
            should_alert, reason = self.processor.process_variance(variance)
            
            if should_alert:
                alerts_to_send.append(variance)
                logger.info(f"Alert triggered: {reason}")
                
                # Send Slack notification if configured
                if self.redash:
                    self.redash.send_slack_alert(variance, reason)
            else:
                logger.info(f"Alert suppressed: {reason}")
        
        return alerts_to_send
    
    def add_historical_exclusion(self, date: str, amount: float, description: str, 
                               category: str, approved_by: str) -> bool:
        """Add a new historical variance exclusion"""
        variance = VarianceRecord(
            date=datetime.fromisoformat(date),
            amount=amount,
            description=description,
            category=category,
            variance_type=VarianceType.APPROVED_HISTORICAL,
            approval_date=datetime.now(),
            approved_by=approved_by
        )
        
        return self.historical_manager.add_historical_variance(variance)
    
    def generate_redash_query(self, base_query: str) -> str:
        """Generate a Redash query that excludes historical variances"""
        # Get all historical exclusions
        conn = sqlite3.connect(self.historical_manager.db_path)
        df = pd.read_sql_query('''
            SELECT category, amount, description 
            FROM historical_variances 
            WHERE variance_type IN ('expected', 'approved_historical')
        ''', conn)
        conn.close()
        
        # Convert to exclusion format
        exclusions = []
        for _, row in df.iterrows():
            exclusions.append({
                'category': row['category'],
                'amount_range': (row['amount'] - 0.01, row['amount'] + 0.01),
                'description_pattern': row['description']
            })
        
        return self.redash.create_filtered_query(base_query, exclusions) if self.redash else base_query

def main():
    """Example usage of the Variance Alert System"""
    
    # Initialize the system
    alert_system = VarianceAlertSystem(
        slack_webhook_url="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    )
    
    # Add some historical variances that should be excluded
    alert_system.add_historical_exclusion(
        date="2024-01-15",
        amount=500.00,
        description="Monthly reconciliation adjustment",
        category="reconciliation",
        approved_by="finance_team"
    )
    
    alert_system.add_historical_exclusion(
        date="2024-02-01", 
        amount=1200.00,
        description="Year-end accrual adjustment",
        category="accruals",
        approved_by="controller"
    )
    
    # Add variance patterns for automatic exclusion
    alert_system.historical_manager.add_variance_pattern(
        pattern_name="small_reconciliation",
        category="reconciliation", 
        amount_threshold=100.00
    )
    
    # Example variance data (this would come from your data source)
    sample_variances = [
        {
            "date": "2024-10-14",
            "amount": 500.00,
            "description": "Monthly reconciliation adjustment", 
            "category": "reconciliation"
        },
        {
            "date": "2024-10-14",
            "amount": 2500.00,
            "description": "Unexpected expense variance",
            "category": "expenses"
        },
        {
            "date": "2024-10-14", 
            "amount": 50.00,
            "description": "Small reconciliation difference",
            "category": "reconciliation"
        }
    ]
    
    # Process the variances
    alerts = alert_system.process_variance_data(sample_variances)
    
    print(f"Processed {len(sample_variances)} variances")
    print(f"Generated {len(alerts)} alerts")
    
    # Generate a filtered Redash query
    base_query = """
    SELECT 
        date,
        category,
        variance_amount,
        description
    FROM variance_report 
    WHERE variance_amount > 0
    ORDER BY date DESC
    """
    
    filtered_query = alert_system.generate_redash_query(base_query)
    print("\nFiltered Redash Query:")
    print(filtered_query)

if __name__ == "__main__":
    main()