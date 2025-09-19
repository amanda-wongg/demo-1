#!/usr/bin/env python3
"""
Command Line Interface for Cash Completeness Monitor
Provides utilities for testing, configuration, and manual operations.
"""

import argparse
import json
import sys
import logging
from datetime import datetime
from pathlib import Path

from main import CashCompletenessMonitor
from config import Config, create_sample_config
from redash_client import RedashClient
from slack_client import SlackClient
from state_manager import StateManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cmd_run_check(args):
    """Run a manual cash completeness check."""
    logger.info("Running manual cash completeness check")
    
    try:
        monitor = CashCompletenessMonitor(args.config)
        result = monitor.run_daily_check()
        
        print(json.dumps(result, indent=2))
        
        if result.get('status') == 'success':
            print(f"\n✅ Check completed successfully")
            print(f"New variances found: {result.get('new_variances_found', 0)}")
            print(f"Alerts sent: {result.get('alerts_sent', 0)}")
        else:
            print(f"\n❌ Check failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to run check: {str(e)}")
        sys.exit(1)


def cmd_test_connections(args):
    """Test connections to Redash and Slack."""
    logger.info("Testing connections")
    
    try:
        config = Config.load_from_file(args.config)
        
        # Test Redash connection
        print("Testing Redash connection...")
        redash_client = RedashClient(config.redash_base_url, config.redash_api_key)
        redash_ok = redash_client.test_connection()
        
        if redash_ok:
            print("✅ Redash connection successful")
        else:
            print("❌ Redash connection failed")
        
        # Test Slack connection
        print("\nTesting Slack connection...")
        slack_client = SlackClient(config.slack_bot_token, config.slack_channel)
        slack_ok = slack_client.test_connection()
        
        if slack_ok:
            print("✅ Slack connection successful")
        else:
            print("❌ Slack connection failed")
        
        # Test queries
        print("\nTesting configured queries...")
        for query in config.redash_queries:
            try:
                query_info = redash_client.get_query_info(query.query_id)
                print(f"✅ Query '{query.name}' (ID: {query.query_id}) - {query_info.get('name', 'Unknown')}")
            except Exception as e:
                print(f"❌ Query '{query.name}' (ID: {query.query_id}) - Error: {str(e)}")
        
        if redash_ok and slack_ok:
            print("\n✅ All connections successful")
        else:
            print("\n❌ Some connections failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        sys.exit(1)


def cmd_create_config(args):
    """Create a sample configuration file."""
    if Path(args.output).exists() and not args.force:
        print(f"Configuration file already exists: {args.output}")
        print("Use --force to overwrite")
        sys.exit(1)
    
    try:
        create_sample_config(args.output)
        print(f"✅ Sample configuration created: {args.output}")
        print("Please edit the configuration file with your actual values")
    except Exception as e:
        logger.error(f"Failed to create configuration: {str(e)}")
        sys.exit(1)


def cmd_validate_config(args):
    """Validate a configuration file."""
    try:
        config = Config.load_from_file(args.config)
        errors = config.validate()
        
        if not errors:
            print("✅ Configuration is valid")
        else:
            print("❌ Configuration validation failed:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        sys.exit(1)


def cmd_show_status(args):
    """Show system status and statistics."""
    try:
        monitor = CashCompletenessMonitor(args.config)
        status = monitor.get_status()
        
        print("=== Cash Completeness Monitor Status ===")
        print(f"System Status: {status.get('system_status', 'Unknown')}")
        print(f"Last Check: {status.get('last_check', 'Never')}")
        print(f"Known Variances: {status.get('known_variances_count', 0)}")
        print(f"Timestamp: {status.get('timestamp', 'Unknown')}")
        
        # Show state manager details
        state_manager = StateManager(monitor.config.state_storage_path)
        metrics = state_manager.get_system_metrics()
        variance_summary = state_manager.get_variance_summary()
        
        print("\n=== System Metrics ===")
        print(f"Total Checks Performed: {metrics.get('total_checks_performed', 0)}")
        print(f"Total Variances Detected: {metrics.get('total_variances_detected', 0)}")
        print(f"Total Alerts Sent: {metrics.get('total_alerts_sent', 0)}")
        
        print("\n=== Variance Summary ===")
        print(f"Total Known Variances: {variance_summary.get('total', 0)}")
        print(f"Unique Accounts: {variance_summary.get('unique_accounts', 0)}")
        print(f"Unique Check Types: {variance_summary.get('unique_check_types', 0)}")
        
        if variance_summary.get('accounts'):
            print(f"Accounts: {', '.join(variance_summary['accounts'])}")
        
        if variance_summary.get('check_types'):
            print(f"Check Types: {', '.join(variance_summary['check_types'])}")
            
    except Exception as e:
        logger.error(f"Failed to get status: {str(e)}")
        sys.exit(1)


def cmd_list_variances(args):
    """List all known variances."""
    try:
        config = Config.load_from_file(args.config)
        state_manager = StateManager(config.state_storage_path)
        known_variances = state_manager.get_known_variances()
        
        if not known_variances:
            print("No known variances found")
            return
        
        print(f"=== Known Variances ({len(known_variances)}) ===")
        
        for variance_id, variance_data in known_variances.items():
            print(f"\nVariance ID: {variance_id}")
            print(f"  Account: {variance_data.get('account', 'Unknown')}")
            print(f"  Check Type: {variance_data.get('check_type', 'Unknown')}")
            print(f"  Amount: {variance_data.get('currency', 'USD')} {variance_data.get('delta_amount', 0):,.2f}")
            print(f"  First Detected: {variance_data.get('first_detected', 'Unknown')}")
            print(f"  Times Seen: {variance_data.get('times_seen', 1)}")
            
    except Exception as e:
        logger.error(f"Failed to list variances: {str(e)}")
        sys.exit(1)


def cmd_remove_variance(args):
    """Remove a known variance by ID."""
    try:
        config = Config.load_from_file(args.config)
        state_manager = StateManager(config.state_storage_path)
        
        if state_manager.remove_known_variance(args.variance_id):
            print(f"✅ Removed variance: {args.variance_id}")
        else:
            print(f"❌ Variance not found: {args.variance_id}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to remove variance: {str(e)}")
        sys.exit(1)


def cmd_cleanup_state(args):
    """Clean up old variances from state."""
    try:
        config = Config.load_from_file(args.config)
        state_manager = StateManager(config.state_storage_path)
        
        removed_count = state_manager.cleanup_old_variances(args.days)
        
        if removed_count > 0:
            print(f"✅ Cleaned up {removed_count} old variances")
        else:
            print("No old variances to clean up")
            
    except Exception as e:
        logger.error(f"Failed to cleanup state: {str(e)}")
        sys.exit(1)


def cmd_send_test_alert(args):
    """Send a test alert to Slack."""
    try:
        config = Config.load_from_file(args.config)
        slack_client = SlackClient(config.slack_bot_token, config.slack_channel)
        
        test_variance = {
            'check_type': 'Test Check',
            'account': 'Test Account',
            'delta_amount': 1234.56,
            'currency': 'USD',
            'detection_date': datetime.now().isoformat(),
            'variance_id': 'test-variance-123'
        }
        
        slack_client.send_formatted_variance_alert(test_variance)
        print("✅ Test alert sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send test alert: {str(e)}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Cash Completeness Monitor CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config', 
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run check command
    run_parser = subparsers.add_parser('run', help='Run a manual cash completeness check')
    run_parser.set_defaults(func=cmd_run_check)
    
    # Test connections command
    test_parser = subparsers.add_parser('test', help='Test connections to Redash and Slack')
    test_parser.set_defaults(func=cmd_test_connections)
    
    # Create config command
    create_parser = subparsers.add_parser('create-config', help='Create a sample configuration file')
    create_parser.add_argument('--output', default='config.json', help='Output file path')
    create_parser.add_argument('--force', action='store_true', help='Overwrite existing file')
    create_parser.set_defaults(func=cmd_create_config)
    
    # Validate config command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration file')
    validate_parser.set_defaults(func=cmd_validate_config)
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    status_parser.set_defaults(func=cmd_show_status)
    
    # List variances command
    list_parser = subparsers.add_parser('list-variances', help='List all known variances')
    list_parser.set_defaults(func=cmd_list_variances)
    
    # Remove variance command
    remove_parser = subparsers.add_parser('remove-variance', help='Remove a known variance')
    remove_parser.add_argument('variance_id', help='Variance ID to remove')
    remove_parser.set_defaults(func=cmd_remove_variance)
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old variances')
    cleanup_parser.add_argument('--days', type=int, default=90, help='Remove variances older than N days')
    cleanup_parser.set_defaults(func=cmd_cleanup_state)
    
    # Test alert command
    alert_parser = subparsers.add_parser('test-alert', help='Send a test alert to Slack')
    alert_parser.set_defaults(func=cmd_send_test_alert)
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()