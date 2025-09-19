"""
AWS Lambda handler for Cash Completeness Monitor
Provides the entry point for running the monitor in AWS Lambda.
"""

import json
import logging
import os
from typing import Dict, Any

from main import CashCompletenessMonitor

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWS Lambda handler function.
    
    Args:
        event: Lambda event data
        context: Lambda context object
        
    Returns:
        Response dictionary
    """
    logger.info("Starting Cash Completeness Monitor Lambda execution")
    
    try:
        # Initialize monitor with environment-based config
        config_path = os.getenv('CONFIG_PATH', '/tmp/config.json')
        
        # If config doesn't exist, try to load from environment variables
        if not os.path.exists(config_path):
            logger.info("Config file not found, attempting to load from environment")
            # The monitor will handle loading from environment variables
        
        monitor = CashCompletenessMonitor(config_path)
        
        # Run the daily check
        result = monitor.run_daily_check()
        
        # Format response for Lambda
        response = {
            'statusCode': 200 if result.get('status') == 'success' else 500,
            'body': json.dumps(result),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        logger.info(f"Lambda execution completed with status: {result.get('status')}")
        return response
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}", exc_info=True)
        
        error_response = {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': str(e),
                'timestamp': context.aws_request_id if context else 'unknown'
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        return error_response


def scheduled_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler specifically for scheduled CloudWatch Events.
    
    Args:
        event: CloudWatch event data
        context: Lambda context object
        
    Returns:
        Response dictionary
    """
    logger.info("Scheduled execution triggered")
    
    # Add scheduled event information to the event
    event['source'] = 'cloudwatch-events'
    event['scheduled'] = True
    
    return lambda_handler(event, context)


def manual_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler for manual invocations (testing, etc.).
    
    Args:
        event: Manual event data
        context: Lambda context object
        
    Returns:
        Response dictionary
    """
    logger.info("Manual execution triggered")
    
    # Add manual execution information
    event['source'] = 'manual'
    event['scheduled'] = False
    
    return lambda_handler(event, context)