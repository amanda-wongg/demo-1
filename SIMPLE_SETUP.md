# Simple Variance Monitor Setup

## What You Need to Do (3 Steps)

### Step 1: Edit the Script
Open `simple_variance_check.py` and change these lines:

```python
# Line 10: Add your Slack webhook URL
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Line 11: Add your database connection
DATABASE_CONNECTION = "your_database_connection_string"

# Lines 35-42: Replace with your actual SQL query
query = f"""
SELECT bank_account, variance, movement, difference
FROM your_actual_table_name 
WHERE your_date_column >= '{start_date}' 
AND your_date_column <= '{end_date}'
AND variance != 0
"""
```

### Step 2: Get Your Slack Webhook
1. Go to https://api.slack.com/apps
2. Create a new app or use existing one
3. Go to "Incoming Webhooks" 
4. Create a webhook for your channel
5. Copy the URL and paste it in the script

### Step 3: Set Up Monday Schedule
Add this to your cron jobs (run `crontab -e`):
```bash
0 9 * * 1 /usr/bin/python3 /workspace/simple_variance_check.py
```

This runs every Monday at 9 AM.

## Test It
```bash
python3 simple_variance_check.py
```

## That's It!
- Every Monday it checks your database
- If variance ≠ 0, you get a Slack message
- If no variances, you get an "all clear" message

Much simpler than the complex system I built before!