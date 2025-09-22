#!/usr/bin/env python3
"""
Simple variance checker - just the basics you need
Run this script every Monday to check for variances and send Slack alerts
"""

import requests
import json
from datetime import datetime, timedelta

# YOUR CONFIGURATION (edit these values)
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
DATABASE_CONNECTION = "your_database_connection_string"

def get_date_range():
    """Get first of month to yesterday"""
    today = datetime.now().date()
    first_of_month = today.replace(day=1)
    yesterday = today - timedelta(days=1)
    return first_of_month, yesterday

def check_for_variances():
    """
    Check your database for variances
    Replace this with your actual database query
    """
    
    # REPLACE THIS SECTION WITH YOUR ACTUAL DATABASE CODE
    # Example for different databases:
    
    # For PostgreSQL:
    # import psycopg2
    # conn = psycopg2.connect(DATABASE_CONNECTION)
    # cursor = conn.cursor()
    
    # For MySQL:
    # import pymysql
    # conn = pymysql.connect(host='your_host', user='your_user', password='your_password', database='your_db')
    # cursor = conn.cursor()
    
    start_date, end_date = get_date_range()
    
    # YOUR SQL QUERY HERE - replace with your actual query
    query = f"""
    SELECT bank_account, variance, movement, difference
    FROM your_table_name 
    WHERE date_column >= '{start_date}' 
    AND date_column <= '{end_date}'
    AND variance != 0
    """
    
    # Execute query and get results
    # cursor.execute(query)
    # results = cursor.fetchall()
    
    # FOR NOW - using your sample data as example
    # Remove this and use real database results
    sample_results = [
        ("Blueridge operations-26", -168.0, 279790.19, -168.0),
        ("Chase operations-3", -10000.0, -318546285.31, 15169668.37)
    ]
    
    return sample_results

def send_slack_alert(variances):
    """Send simple Slack message"""
    if not variances:
        message = "✅ No variances found in bank reconciliation"
    else:
        message = f"🚨 VARIANCE ALERT: {len(variances)} accounts have variances:\n\n"
        for account, variance, movement, difference in variances:
            message += f"• {account}: ${variance:,.2f}\n"
    
    # Send to Slack
    payload = {"text": message}
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    
    if response.status_code == 200:
        print("✅ Slack alert sent successfully")
    else:
        print(f"❌ Failed to send Slack alert: {response.status_code}")

def main():
    """Main function - this is what runs every Monday"""
    print("Checking for variances...")
    
    # Get variances from database
    variances = check_for_variances()
    
    # Send Slack alert
    send_slack_alert(variances)
    
    print(f"Found {len(variances)} variances")

if __name__ == "__main__":
    main()