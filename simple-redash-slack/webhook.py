#!/usr/bin/env python3
"""
Simple Redash to Slack Webhook
Just run queries and send results to Slack - no AI, no complexity
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration - just change these values
REDASH_URL = "https://your-redash-instance.com"
REDASH_API_KEY = "your-api-key-here"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

def run_redash_query(query_id):
    """Run a Redash query and get results"""
    headers = {'Authorization': f'Key {REDASH_API_KEY}'}
    
    # Refresh the query
    refresh_url = f"{REDASH_URL}/api/queries/{query_id}/refresh"
    response = requests.post(refresh_url, headers=headers)
    
    if response.status_code != 200:
        return None
    
    job = response.json()
    job_id = job['job']['id']
    
    # Wait for results (simple polling)
    for _ in range(30):  # Wait up to 30 seconds
        job_url = f"{REDASH_URL}/api/jobs/{job_id}"
        job_response = requests.get(job_url, headers=headers)
        
        if job_response.status_code == 200:
            job_data = job_response.json()
            if job_data['job']['status'] == 3:  # Completed
                result_id = job_data['job']['query_result_id']
                break
        
        time.sleep(1)
    else:
        return None
    
    # Get the actual results
    result_url = f"{REDASH_URL}/api/query_results/{result_id}"
    result_response = requests.get(result_url, headers=headers)
    
    if result_response.status_code == 200:
        return result_response.json()
    
    return None

def send_to_slack(query_name, data):
    """Send results to Slack"""
    if not data or 'data' not in data or 'rows' not in data['data']:
        message = f"❌ No data returned for query: {query_name}"
    else:
        rows = data['data']['rows']
        row_count = len(rows)
        
        # Create simple message
        message = f"📊 *{query_name}*\n"
        message += f"Rows returned: {row_count}\n"
        
        # Show first few rows
        if rows:
            message += "\n*Sample data:*\n"
            for i, row in enumerate(rows[:3]):  # First 3 rows
                message += f"Row {i+1}: {json.dumps(row, default=str)}\n"
            
            if row_count > 3:
                message += f"... and {row_count - 3} more rows"
    
    # Send to Slack
    payload = {
        "text": message,
        "username": "Redash Bot",
        "icon_emoji": ":bar_chart:"
    }
    
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    return response.status_code == 200

def main():
    """Main function - customize this for your queries"""
    
    # List your queries here - just add query IDs and names
    queries = [
        {"id": 123, "name": "Daily Sales Report"},
        {"id": 456, "name": "User Signups This Week"},
        # Add more queries here
    ]
    
    print(f"Running {len(queries)} queries...")
    
    for query in queries:
        print(f"Running query: {query['name']}")
        
        # Run the query
        results = run_redash_query(query['id'])
        
        # Send to Slack
        if send_to_slack(query['name'], results):
            print(f"✅ Sent {query['name']} to Slack")
        else:
            print(f"❌ Failed to send {query['name']} to Slack")
        
        # Wait a bit between queries
        time.sleep(2)
    
    print("Done!")

if __name__ == "__main__":
    main()