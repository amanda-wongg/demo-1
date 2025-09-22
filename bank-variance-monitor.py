#!/usr/bin/env python3
"""
Bank Reconciliation Variance Monitor
Checks Redash query for non-zero variance and sends Slack alerts
"""

import requests
import json
import time
from datetime import datetime

# 🔧 CONFIGURATION - UPDATE THESE
REDASH_URL = "https://your-redash-instance.com"
REDASH_API_KEY = "your-redash-api-key-here"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
QUERY_ID = 123  # Your Redash query ID

def run_redash_query(query_id):
    """Run the Redash query and get results"""
    print(f"🔄 Running Redash query {query_id}...")
    
    headers = {'Authorization': f'Key {REDASH_API_KEY}'}
    
    # Refresh the query
    refresh_url = f"{REDASH_URL}/api/queries/{query_id}/refresh"
    response = requests.post(refresh_url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to refresh query: {response.status_code}")
        return None
    
    job = response.json()
    job_id = job['job']['id']
    print(f"📋 Job started: {job_id}")
    
    # Wait for completion
    for attempt in range(30):  # Wait up to 30 seconds
        job_url = f"{REDASH_URL}/api/jobs/{job_id}"
        job_response = requests.get(job_url, headers=headers)
        
        if job_response.status_code == 200:
            job_data = job_response.json()
            status = job_data['job']['status']
            
            if status == 3:  # Completed
                result_id = job_data['job']['query_result_id']
                print(f"✅ Query completed! Getting results...")
                break
            elif status == 4:  # Failed
                print(f"❌ Query failed")
                return None
        
        print(f"⏳ Waiting... ({attempt + 1}/30)")
        time.sleep(1)
    else:
        print(f"⏰ Query timeout")
        return None
    
    # Get the results
    result_url = f"{REDASH_URL}/api/query_results/{result_id}"
    result_response = requests.get(result_url, headers=headers)
    
    if result_response.status_code != 200:
        print(f"❌ Failed to get results: {result_response.status_code}")
        return None
    
    results = result_response.json()
    rows = results.get('query_result', {}).get('data', {}).get('rows', [])
    print(f"📊 Retrieved {len(rows)} bank accounts")
    
    return rows

def check_variances(data):
    """Check for non-zero variances and return problematic accounts"""
    if not data:
        return []
    
    problem_accounts = []
    
    for row in data:
        variance = float(row.get('variance', 0))
        
        # Alert if variance is not exactly 0.00
        if variance != 0.0:
            problem_accounts.append({
                'bank_account': row.get('bank_account', 'Unknown'),
                'variance': variance,
                'bt_date_1': row.get('bt_date_1'),
                'bt_date_2': row.get('bt_date_2'),
                'movement': float(row.get('movement', 0)),
                'difference': float(row.get('difference', 0))
            })
    
    return problem_accounts

def format_slack_alert(problem_accounts):
    """Format the Slack alert message"""
    if not problem_accounts:
        return {
            "text": "✅ *Bank Reconciliation: All Clear*\nAll accounts have zero variance.",
            "username": "Bank Variance Monitor",
            "icon_emoji": ":white_check_mark:"
        }
    
    # Create alert message
    header = f"🚨 *Bank Reconciliation Alert*\n{len(problem_accounts)} account(s) with non-zero variance detected!\n"
    
    details = ""
    total_variance = 0
    
    for account in problem_accounts:
        variance = account['variance']
        total_variance += abs(variance)
        
        # Format variance with proper sign and currency
        variance_str = f"${variance:,.2f}" if variance >= 0 else f"-${abs(variance):,.2f}"
        
        details += f"\n🏦 *{account['bank_account']}*\n"
        details += f"   💰 Variance: `{variance_str}`\n"
        details += f"   📅 Period: {account['bt_date_1']} → {account['bt_date_2']}\n"
        details += f"   📊 Movement: ${account['movement']:,.2f}\n"
        
        if len(details) > 2500:  # Slack message limit
            remaining = len(problem_accounts) - problem_accounts.index(account) - 1
            if remaining > 0:
                details += f"\n_...and {remaining} more accounts_"
            break
    
    footer = f"\n📈 *Total Absolute Variance: ${total_variance:,.2f}*"
    footer += f"\n🕐 Checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    message = header + details + footer
    
    return {
        "text": message,
        "username": "Bank Variance Monitor",
        "icon_emoji": ":warning:"
    }

def send_to_slack(message_data):
    """Send alert to Slack"""
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=message_data)
        
        if response.status_code == 200:
            print("✅ Alert sent to Slack successfully")
            return True
        else:
            print(f"❌ Failed to send to Slack: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending to Slack: {e}")
        return False

def main():
    """Main monitoring function"""
    print("🚀 Starting Bank Variance Monitor...")
    print(f"📊 Checking query {QUERY_ID} for non-zero variances...")
    
    try:
        # Get data from Redash
        data = run_redash_query(QUERY_ID)
        
        if data is None:
            # Send error alert
            error_message = {
                "text": "❌ *Bank Variance Monitor Error*\nFailed to retrieve data from Redash query.",
                "username": "Bank Variance Monitor",
                "icon_emoji": ":x:"
            }
            send_to_slack(error_message)
            return
        
        # Check for variances
        problem_accounts = check_variances(data)
        
        print(f"🔍 Found {len(problem_accounts)} accounts with non-zero variance")
        
        # Always send a message (either alert or all-clear)
        message = format_slack_alert(problem_accounts)
        
        if send_to_slack(message):
            if problem_accounts:
                print(f"🚨 VARIANCE ALERT: {len(problem_accounts)} accounts need attention")
            else:
                print("✅ All accounts reconciled properly")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        
        # Send error alert
        error_message = {
            "text": f"❌ *Bank Variance Monitor Error*\n```{str(e)}```",
            "username": "Bank Variance Monitor",
            "icon_emoji": ":x:"
        }
        send_to_slack(error_message)

if __name__ == "__main__":
    main()