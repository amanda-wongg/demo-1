"""
Google Cloud Functions handler for Cash Completeness Monitor
Provides the entry point for running the monitor in Google Cloud Functions.
"""

import json
import logging
import os
from typing import Dict, Any
from flask import Request

from main import CashCompletenessMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cash_monitor_http(request: Request) -> tuple:
    """
    HTTP Cloud Function entry point.
    
    Args:
        request: Flask request object
        
    Returns:
        Tuple of (response_data, status_code, headers)
    """
    logger.info("Starting Cash Completeness Monitor Cloud Function execution")
    
    try:
        # Initialize monitor
        config_path = os.getenv('CONFIG_PATH', 'config.json')
        monitor = CashCompletenessMonitor(config_path)
        
        # Run the daily check
        result = monitor.run_daily_check()
        
        status_code = 200 if result.get('status') == 'success' else 500
        headers = {'Content-Type': 'application/json'}
        
        logger.info(f"Cloud Function execution completed with status: {result.get('status')}")
        return json.dumps(result), status_code, headers
        
    except Exception as e:
        logger.error(f"Cloud Function execution failed: {str(e)}", exc_info=True)
        
        error_response = {
            'status': 'error',
            'error': str(e),
            'timestamp': request.headers.get('Function-Execution-Id', 'unknown')
        }
        
        return json.dumps(error_response), 500, {'Content-Type': 'application/json'}


def cash_monitor_pubsub(event, context):
    """
    Pub/Sub triggered Cloud Function entry point.
    
    Args:
        event: Pub/Sub event data
        context: Cloud Function context
        
    Returns:
        None (Pub/Sub functions don't return responses)
    """
    logger.info("Starting scheduled Cash Completeness Monitor execution")
    
    try:
        # Initialize monitor
        config_path = os.getenv('CONFIG_PATH', 'config.json')
        monitor = CashCompletenessMonitor(config_path)
        
        # Run the daily check
        result = monitor.run_daily_check()
        
        logger.info(f"Scheduled execution completed with status: {result.get('status')}")
        
        if result.get('status') != 'success':
            # Log error for monitoring systems to pick up
            logger.error(f"Scheduled execution failed: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        logger.error(f"Scheduled execution failed: {str(e)}", exc_info=True)
        raise  # Re-raise to mark the function execution as failed


def cash_monitor_scheduler(request: Request) -> tuple:
    """
    Cloud Scheduler HTTP target entry point.
    
    Args:
        request: Flask request object
        
    Returns:
        Tuple of (response_data, status_code, headers)
    """
    logger.info("Starting scheduled Cash Completeness Monitor execution via HTTP")
    
    # Verify the request is from Cloud Scheduler (optional security check)
    if request.headers.get('User-Agent', '').startswith('Google-Cloud-Scheduler'):
        logger.info("Request verified as coming from Cloud Scheduler")
    else:
        logger.warning("Request may not be from Cloud Scheduler")
    
    return cash_monitor_http(request)