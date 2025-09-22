# Bank Variance Monitor Setup

## What This Does
- ✅ Runs your Redash bank reconciliation query
- ✅ Checks every account's variance column
- ✅ Sends Slack alert if ANY variance is not $0.00
- ✅ Shows which accounts have problems and how much

## Quick Setup (5 minutes)

### Step 1: Get Your Slack Webhook
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name it "Bank Variance Monitor"
4. Go to "Incoming Webhooks" → Turn ON
5. Click "Add New Webhook to Workspace"
6. Choose your channel (e.g., #finance-alerts)
7. Copy the webhook URL

### Step 2: Get Your Redash Info
1. **API Key**: In Redash, go to your profile → Settings → API Key
2. **Query ID**: Look at your query URL: `https://redash.com/queries/123/` (123 is your query ID)

### Step 3: Configure the Script
Edit `bank-variance-monitor.py` and change these lines:

```python
REDASH_URL = "https://your-redash-instance.com"     # Your Redash URL
REDASH_API_KEY = "your-redash-api-key-here"         # From Step 2
SLACK_WEBHOOK_URL = "https://hooks.slack.com/..."   # From Step 1
QUERY_ID = 123                                      # Your query ID from Step 2
```

### Step 4: Test It
```bash
# Install requirements
pip install requests

# Run the monitor
python bank-variance-monitor.py
```

## What You'll See in Slack

### ✅ When everything is good:
```
✅ Bank Reconciliation: All Clear
All accounts have zero variance.
```

### 🚨 When there are problems:
```
🚨 Bank Reconciliation Alert
2 account(s) with non-zero variance detected!

🏦 Chase operations-3
   💰 Variance: -$10,000.00
   📅 Period: 2025-08-31 → 2025-09-21
   📊 Movement: -$318,546,285.31

🏦 Chase wire_in-9
   💰 Variance: $3,227.30
   📅 Period: 2025-08-31 → 2025-09-21
   📊 Movement: -$4,802.77

📈 Total Absolute Variance: $13,227.30
🕐 Checked: 2024-12-15 14:30:22
```

## Automation Options

### Run Every Hour
```bash
# Add to crontab (crontab -e)
0 * * * * cd /path/to/script && python bank-variance-monitor.py
```

### Run Every 30 Minutes During Business Hours
```bash
# 9 AM to 5 PM, every 30 minutes, weekdays only
0,30 9-17 * * 1-5 cd /path/to/script && python bank-variance-monitor.py
```

### Run Daily at 9 AM
```bash
0 9 * * * cd /path/to/script && python bank-variance-monitor.py
```

## Troubleshooting

### ❌ "Failed to refresh query"
- Check your Redash URL and API key
- Make sure the query ID is correct
- Verify you can access the query in Redash

### ❌ "Failed to send to Slack"
- Test your webhook: `curl -X POST -H 'Content-type: application/json' --data '{"text":"Test"}' YOUR_WEBHOOK_URL`
- Check the webhook URL is complete

### ❌ No variance alerts when you expect them
- Check that your query returns a column named exactly `variance`
- Verify the variance values are numbers (not text)

## Customization

### Change Alert Threshold
If you want to alert only when variance is above a certain amount:

```python
# In the check_variances function, change this line:
if variance != 0.0:

# To something like:
if abs(variance) > 100.0:  # Alert only if variance > $100
```

### Add More Details
You can include more columns from your query in the alert:

```python
# In the format_slack_alert function, add lines like:
details += f"   🔄 Reconciled: ${account.get('reconciled_payment_records', 0):,.2f}\n"
```

## That's It!
Simple, focused, and does exactly what you need - monitors bank variance and alerts when something's wrong.