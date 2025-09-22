#!/usr/bin/env python3
"""
Simple CSV Variance Checker
Just export your Redash query to CSV and run this script
"""
import csv
import requests

# Configuration
CSV_FILE_PATH = "bank_reconciliation.csv"  # Path to your exported CSV
SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

def check_csv_variance():
    problems = []
    
    try:
        with open(CSV_FILE_PATH, 'r') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                variance = float(row.get('variance', 0))
                if variance != 0:
                    problems.append({
                        'account': row.get('bank_account', 'Unknown'),
                        'variance': variance
                    })
        
        # Send to Slack
        if problems:
            message = f"🚨 {len(problems)} accounts with variance:\n"
            for p in problems[:5]:  # First 5
                message += f"• {p['account']}: ${p['variance']:,.2f}\n"
        else:
            message = "✅ All accounts reconciled properly"
        
        requests.post(SLACK_WEBHOOK, json={"text": message})
        print(f"✅ Checked {CSV_FILE_PATH}: {len(problems)} variance(s) found")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_csv_variance()