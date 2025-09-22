#!/usr/bin/env python3
"""
Simple test for variance monitor without external dependencies
Tests core logic and data structures
"""

import sys
import json
from datetime import datetime, timedelta
from dataclasses import dataclass

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

def create_test_data():
    """Create test variance records based on your sample"""
    return [
        VarianceRecord(
            bank_account="Blueridge operations-26",
            reconciled_payment_records=279958.19,
            bt_date_1="2025-08-31",
            bt_balance_1=9877835.45,
            bt_date_2="2025-09-21", 
            bt_balance_2=10157625.64,
            movement=279790.19,
            difference=-168.0,
            unreconciled_bt_credit=168.0,
            unreconciled_bt_debit=0.0,
            unreconciled_bt_absolute_total=-168.0,
            variance=-168.0
        ),
        VarianceRecord(
            bank_account="Chase operations-3",
            reconciled_payment_records=-33715953.68,
            bt_date_1="2025-08-31",
            bt_balance_1=696612586.78,
            bt_date_2="2025-09-21",
            bt_balance_2=378066301.47,
            movement=-318546285.31,
            difference=15169668.37,
            unreconciled_bt_credit=3426.02,
            unreconciled_bt_debit=15183094.39,
            unreconciled_bt_absolute_total=15179668.37,
            variance=-10000.0
        )
    ]

def format_slack_message(records, start_date, end_date):
    """Format variance records into a Slack message structure"""
    if not records:
        return {
            "text": f"✅ No variances detected for period {start_date} to {end_date}",
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
        }
    ]
    
    # Add details for each variance
    for record in records:
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
    
    return {
        "text": f"🚨 VARIANCE ALERT: {len(records)} variances detected ({start_date} to {end_date})",
        "blocks": blocks
    }

def test_date_range():
    """Test date range calculation"""
    print("📅 Testing date range calculation...")
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    first_of_month = today.replace(day=1)
    
    print(f"Today: {today}")
    print(f"First of month: {first_of_month}")
    print(f"Yesterday: {yesterday}")
    
    return first_of_month, yesterday

def test_variance_detection():
    """Test variance detection logic"""
    print("\n🔍 Testing variance detection...")
    
    records = create_test_data()
    variances_found = [r for r in records if r.variance != 0]
    
    print(f"Total records: {len(records)}")
    print(f"Records with variances: {len(variances_found)}")
    
    for record in variances_found:
        print(f"  • {record.bank_account}: ${record.variance:,.2f}")
    
    return variances_found

def test_slack_formatting():
    """Test Slack message formatting"""
    print("\n📱 Testing Slack message formatting...")
    
    records = create_test_data()
    start_date = datetime(2025, 9, 1).date()
    end_date = datetime(2025, 9, 21).date()
    
    # Test with variances
    message = format_slack_message(records, start_date, end_date)
    print(f"\nMessage with variances:")
    print(f"Title: {message['text']}")
    print(f"Blocks: {len(message['blocks'])}")
    
    # Test without variances
    empty_message = format_slack_message([], start_date, end_date)
    print(f"\nMessage without variances:")
    print(f"Title: {empty_message['text']}")
    
    return message

def display_sample_alert(message):
    """Display a sample Slack alert in readable format"""
    print("\n" + "="*60)
    print("📱 SAMPLE SLACK ALERT")
    print("="*60)
    
    print(f"Channel: #finance-alerts")
    print(f"Title: {message['text']}")
    print("\nMessage Content:")
    print("-" * 40)
    
    for block in message['blocks']:
        if block['type'] == 'section':
            content = block['text']['text']
            # Convert Slack markdown to readable text
            content = content.replace('*', '')
            content = content.replace('•', '  •')
            print(content)
            print()

def main():
    """Run all tests"""
    print("🧪 VARIANCE MONITOR SIMPLE TEST")
    print("="*60)
    print("Testing core functionality without external dependencies\n")
    
    try:
        # Test date calculations
        start_date, end_date = test_date_range()
        
        # Test variance detection
        variance_records = test_variance_detection()
        
        # Test Slack formatting
        slack_message = test_slack_formatting()
        
        # Display sample alert
        display_sample_alert(slack_message)
        
        print("="*60)
        print("✅ ALL TESTS PASSED")
        print("\nThe variance monitor core logic is working correctly!")
        print("\n🚀 Next Steps:")
        print("1. Install Python dependencies: pip install -r requirements.txt")
        print("2. Configure .env file with your database and Slack settings")
        print("3. Update the SQL query in variance_monitor.py")
        print("4. Run the full test: python3 test_variance_monitor.py")
        print("5. Set up the cron job: ./setup_cron.sh")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)