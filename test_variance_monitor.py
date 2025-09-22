#!/usr/bin/env python3
"""
Test script for the variance monitor
Allows testing without waiting for Monday or modifying cron jobs
"""

import os
import sys
from datetime import datetime, timedelta
from variance_monitor import VarianceMonitor, VarianceRecord

def create_test_data():
    """Create some test variance records for demonstration"""
    return [
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

def test_slack_message_formatting():
    """Test Slack message formatting with sample data"""
    print("🧪 Testing Slack message formatting...")
    
    monitor = VarianceMonitor()
    test_records = create_test_data()
    start_date = datetime.now().date().replace(day=1)
    end_date = datetime.now().date() - timedelta(days=1)
    
    # Test with variances
    message = monitor.format_variance_message(test_records, start_date, end_date)
    print("\n📱 Sample Slack message with variances:")
    print("=" * 50)
    print(f"Text: {message['text']}")
    print("\nBlocks:")
    for i, block in enumerate(message['blocks']):
        if block['type'] == 'section':
            print(f"Block {i}: {block['text']['text']}")
        elif block['type'] == 'divider':
            print(f"Block {i}: [Divider]")
    
    # Test without variances
    message_no_variance = monitor.format_variance_message([], start_date, end_date)
    print("\n✅ Sample Slack message without variances:")
    print("=" * 50)
    print(f"Text: {message_no_variance['text']}")
    print(f"Block: {message_no_variance['blocks'][0]['text']['text']}")

def test_configuration():
    """Test configuration validation"""
    print("\n🔧 Testing configuration...")
    
    monitor = VarianceMonitor()
    
    print(f"Database connection string: {'✅ Set' if monitor.db_connection_string else '❌ Not set'}")
    print(f"Slack webhook URL: {'✅ Set' if monitor.slack_webhook_url else '❌ Not set'}")
    print(f"Slack channel: {monitor.slack_channel}")
    
    if not monitor.validate_config():
        print("\n⚠️  Configuration is incomplete. Please set environment variables:")
        print("   - DATABASE_CONNECTION_STRING")
        print("   - SLACK_WEBHOOK_URL")
        print("   - SLACK_CHANNEL (optional)")
        return False
    
    print("✅ Configuration is valid")
    return True

def test_database_connection():
    """Test database connection"""
    print("\n🗄️  Testing database connection...")
    
    monitor = VarianceMonitor()
    if not monitor.db_connection_string:
        print("❌ No database connection string provided")
        return False
    
    try:
        if monitor.connect_to_database():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_date_range():
    """Test date range calculation"""
    print("\n📅 Testing date range calculation...")
    
    monitor = VarianceMonitor()
    start_date, end_date = monitor.get_date_range()
    
    print(f"Start date (first of month): {start_date}")
    print(f"End date (yesterday): {end_date}")
    
    # Validate dates
    today = datetime.now().date()
    expected_start = today.replace(day=1)
    expected_end = today - timedelta(days=1)
    
    if start_date == expected_start and end_date == expected_end:
        print("✅ Date range calculation is correct")
        return True
    else:
        print("❌ Date range calculation is incorrect")
        return False

def run_full_test():
    """Run the complete variance check (requires full configuration)"""
    print("\n🚀 Running full variance check test...")
    
    monitor = VarianceMonitor()
    
    if not monitor.validate_config():
        print("❌ Cannot run full test - configuration incomplete")
        return False
    
    try:
        success = monitor.run_variance_check()
        if success:
            print("✅ Full variance check completed successfully")
        else:
            print("❌ Full variance check failed")
        return success
    except Exception as e:
        print(f"❌ Full test error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Variance Monitor Test Suite")
    print("=" * 40)
    
    tests = [
        ("Configuration", test_configuration),
        ("Date Range", test_date_range),
        ("Slack Formatting", test_slack_message_formatting),
        ("Database Connection", test_database_connection),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Results Summary:")
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    # Offer to run full test if configuration is complete
    if results.get("Configuration", False) and results.get("Database Connection", False):
        response = input("\n🤔 Configuration looks good. Run full variance check? (y/N): ")
        if response.lower().startswith('y'):
            run_full_test()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)