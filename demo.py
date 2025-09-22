#!/usr/bin/env python3
"""
Demo script for the variance monitor
Shows how the system works with sample data (no database required)
"""

import json
from datetime import datetime, timedelta
from variance_monitor import VarianceRecord

def create_demo_data():
    """Create realistic demo variance records based on your sample"""
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
        ),
        VarianceRecord(
            bank_account="Chase wire_in-9",
            reconciled_payment_records=6415109.47,
            bt_date_1="2025-08-31",
            bt_balance_1=97544.41,
            bt_date_2="2025-09-21",
            bt_balance_2=92741.64,
            movement=-4802.77,
            difference=-6419912.24,
            unreconciled_bt_credit=6487438.26,
            unreconciled_bt_debit=64298.72,
            unreconciled_bt_absolute_total=-6423139.54,
            variance=3227.3
        ),
        VarianceRecord(
            bank_account="PNC operations-16",
            reconciled_payment_records=56.09,
            bt_date_1="2025-08-31",
            bt_balance_1=1600004.74,
            bt_date_2="2025-09-21",
            bt_balance_2=1600004.74,
            movement=0.0,
            difference=-56.09,
            unreconciled_bt_credit=56.09,
            unreconciled_bt_debit=0.0,
            unreconciled_bt_absolute_total=-56.09,
            variance=-56.09
        )
    ]

def demo_slack_message():
    """Demonstrate Slack message formatting"""
    print("📱 SLACK MESSAGE DEMO")
    print("=" * 60)
    
    # Import here to avoid dependency issues
    from variance_monitor import VarianceMonitor
    
    monitor = VarianceMonitor()
    demo_records = create_demo_data()
    start_date = datetime(2025, 9, 1).date()
    end_date = datetime(2025, 9, 21).date()
    
    # Generate message
    message = monitor.format_variance_message(demo_records, start_date, end_date)
    
    print(f"📧 Slack Message Preview:")
    print(f"Channel: #finance-alerts")
    print(f"Title: {message['text']}")
    print("\n📄 Message Content:")
    print("-" * 40)
    
    for block in message['blocks']:
        if block['type'] == 'section':
            content = block['text']['text']
            # Convert Slack markdown to readable text
            content = content.replace('*', '**')
            content = content.replace('•', '  •')
            print(content)
        elif block['type'] == 'divider':
            print("-" * 40)
    
    print("\n🔍 Raw JSON (for webhook):")
    print(json.dumps(message, indent=2))

def demo_no_variances():
    """Demonstrate message when no variances found"""
    print("\n✅ NO VARIANCES DEMO")
    print("=" * 60)
    
    from variance_monitor import VarianceMonitor
    
    monitor = VarianceMonitor()
    start_date = datetime(2025, 9, 1).date()
    end_date = datetime(2025, 9, 21).date()
    
    # Generate message with empty records
    message = monitor.format_variance_message([], start_date, end_date)
    
    print(f"📧 Slack Message Preview:")
    print(f"Title: {message['text']}")
    print("\n📄 Message Content:")
    print("-" * 40)
    print(message['blocks'][0]['text']['text'].replace('*', '**'))

def demo_summary():
    """Show summary statistics"""
    print("\n📊 VARIANCE ANALYSIS DEMO")
    print("=" * 60)
    
    records = create_demo_data()
    
    total_accounts = len(records)
    total_variance = sum(abs(r.variance) for r in records)
    largest_variance = max(records, key=lambda r: abs(r.variance))
    positive_variances = [r for r in records if r.variance > 0]
    negative_variances = [r for r in records if r.variance < 0]
    
    print(f"📈 Summary Statistics:")
    print(f"  • Total accounts with variances: {total_accounts}")
    print(f"  • Total absolute variance: ${total_variance:,.2f}")
    print(f"  • Positive variances: {len(positive_variances)}")
    print(f"  • Negative variances: {len(negative_variances)}")
    print(f"  • Largest variance: ${largest_variance.variance:,.2f} ({largest_variance.bank_account})")
    
    print(f"\n📋 Detailed Breakdown:")
    for record in records:
        status = "🔴" if record.variance < 0 else "🟡"
        print(f"  {status} {record.bank_account}")
        print(f"     Variance: ${record.variance:,.2f}")
        print(f"     Movement: ${record.movement:,.2f}")
        print(f"     Difference: ${record.difference:,.2f}")
        print()

def main():
    """Main demo function"""
    print("🎭 VARIANCE MONITOR DEMO")
    print("=" * 60)
    print("This demo shows how the variance monitor works")
    print("using sample data from your query results.")
    print()
    
    try:
        demo_summary()
        demo_slack_message()
        demo_no_variances()
        
        print("\n" + "=" * 60)
        print("✨ DEMO COMPLETE")
        print()
        print("🚀 Next Steps:")
        print("1. Configure your .env file with database and Slack settings")
        print("2. Update the SQL query in variance_monitor.py for your table")
        print("3. Run: python3 test_variance_monitor.py")
        print("4. Run: ./setup_cron.sh")
        print()
        print("📖 See VARIANCE_MONITOR_README.md for full documentation")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("Make sure you have the required dependencies installed:")
        print("pip3 install -r requirements.txt")

if __name__ == "__main__":
    main()