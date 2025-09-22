# Complete Walkthrough: Simple Webhook Setup

## Step 1: Create Slack Webhook (3 minutes)

### 1.1 Create Slack App
1. Go to https://api.slack.com/apps
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. App Name: `Redash Bot`
5. Pick your workspace
6. Click **"Create App"**

### 1.2 Enable Incoming Webhooks
1. In your new app, click **"Incoming Webhooks"** (left sidebar)
2. Toggle **"Activate Incoming Webhooks"** to **ON**
3. Click **"Add New Webhook to Workspace"**
4. Choose the channel where you want reports (e.g., `#data-reports`)
5. Click **"Allow"**

### 1.3 Copy Webhook URL
- You'll see a webhook URL like: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`
- **Copy this URL** - you'll need it in Step 3

## Step 2: Get Redash API Key (2 minutes)

### 2.1 Find Your API Key
1. Log into your Redash instance
2. Click your **profile picture** (top right corner)
3. Click **"Settings"** or **"Account"**
4. Look for **"API Key"** tab or section
5. **Copy your API key** (looks like: `abc123def456...`)

### 2.2 Find Query IDs
1. Go to any query in Redash
2. Look at the URL: `https://your-redash.com/queries/123/source`
3. The number `123` is your Query ID
4. **Write down the Query IDs** you want to automate

## Step 3: Setup the Script (3 minutes)

### 3.1 Download Python Script
Save this as `redash_to_slack.py`:

```python
#!/usr/bin/env python3
import requests
import json
import time

# 🔧 CONFIGURATION - CHANGE THESE VALUES
REDASH_URL = "https://your-redash-instance.com"  # ← Your Redash URL
REDASH_API_KEY = "your-api-key-here"             # ← Your API key from Step 2
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"  # ← From Step 1

def run_query_and_send_to_slack(query_id, query_name):
    """Run a Redash query and send results to Slack"""
    print(f"🔄 Running query: {query_name}")
    
    # Step 1: Refresh the query
    headers = {'Authorization': f'Key {REDASH_API_KEY}'}
    refresh_url = f"{REDASH_URL}/api/queries/{query_id}/refresh"
    
    try:
        response = requests.post(refresh_url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to refresh query {query_id}: {response.status_code}")
            return False
        
        job = response.json()
        job_id = job['job']['id']
        print(f"📋 Job started: {job_id}")
        
        # Step 2: Wait for query to complete
        for attempt in range(30):  # Wait up to 30 seconds
            job_url = f"{REDASH_URL}/api/jobs/{job_id}"
            job_response = requests.get(job_url, headers=headers)
            
            if job_response.status_code == 200:
                job_data = job_response.json()
                status = job_data['job']['status']
                
                if status == 3:  # Completed successfully
                    result_id = job_data['job']['query_result_id']
                    print(f"✅ Query completed! Result ID: {result_id}")
                    break
                elif status == 4:  # Failed
                    print(f"❌ Query failed")
                    return False
                else:
                    print(f"⏳ Waiting... (attempt {attempt + 1}/30)")
            
            time.sleep(1)
        else:
            print(f"⏰ Query timeout after 30 seconds")
            return False
        
        # Step 3: Get the results
        result_url = f"{REDASH_URL}/api/query_results/{result_id}"
        result_response = requests.get(result_url, headers=headers)
        
        if result_response.status_code != 200:
            print(f"❌ Failed to get results: {result_response.status_code}")
            return False
        
        results = result_response.json()
        rows = results.get('query_result', {}).get('data', {}).get('rows', [])
        
        # Step 4: Format message for Slack
        if not rows:
            message = f"📊 *{query_name}*\n❌ No data returned"
        else:
            message = f"📊 *{query_name}*\n"
            message += f"📈 Rows returned: {len(rows)}\n"
            message += f"🔗 <{REDASH_URL}/queries/{query_id}|View in Redash>\n\n"
            
            # Show first 3 rows as preview
            message += "*Sample data:*\n"
            for i, row in enumerate(rows[:3]):
                row_text = " | ".join([f"{k}: {v}" for k, v in row.items()])
                message += f"`{i+1}.` {row_text}\n"
            
            if len(rows) > 3:
                message += f"_...and {len(rows) - 3} more rows_"
        
        # Step 5: Send to Slack
        slack_payload = {
            "text": message,
            "username": "Redash Bot",
            "icon_emoji": ":bar_chart:"
        }
        
        slack_response = requests.post(SLACK_WEBHOOK_URL, json=slack_payload)
        
        if slack_response.status_code == 200:
            print(f"✅ Sent '{query_name}' to Slack!")
            return True
        else:
            print(f"❌ Failed to send to Slack: {slack_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Main function - Add your queries here"""
    
    # 🎯 ADD YOUR QUERIES HERE
    queries = [
        {"id": 123, "name": "Daily Sales Report"},      # ← Replace 123 with real query ID
        {"id": 456, "name": "Weekly User Signups"},     # ← Replace 456 with real query ID
        {"id": 789, "name": "Revenue Dashboard"},       # ← Add more queries as needed
    ]
    
    print(f"🚀 Starting Redash to Slack automation...")
    print(f"📋 Running {len(queries)} queries\n")
    
    success_count = 0
    for query in queries:
        if run_query_and_send_to_slack(query['id'], query['name']):
            success_count += 1
        
        # Wait 2 seconds between queries to be nice to the API
        time.sleep(2)
        print()  # Empty line for readability
    
    print(f"🎉 Done! {success_count}/{len(queries)} queries sent successfully")

if __name__ == "__main__":
    main()
```

### 3.2 Configure the Script
1. Open `redash_to_slack.py` in any text editor
2. **Change line 6**: Replace with your Redash URL
3. **Change line 7**: Replace with your API key from Step 2  
4. **Change line 8**: Replace with your webhook URL from Step 1
5. **Change the queries list** (around line 95): Replace the example query IDs with your real ones

### 3.3 Test the Script
```bash
# Install required library
pip install requests

# Run the script
python redash_to_slack.py
```

## Step 4: Automate It (2 minutes)

### Option A: Windows Task Scheduler
1. Open **Task Scheduler**
2. Click **"Create Basic Task"**
3. Name: `Redash to Slack`
4. Trigger: **Daily** at 9:00 AM
5. Action: **Start a program**
   - Program: `python.exe`
   - Arguments: `C:\path\to\your\redash_to_slack.py`
6. Click **Finish**

### Option B: Mac/Linux Cron
```bash
# Edit crontab
crontab -e

# Add this line for daily at 9 AM:
0 9 * * * cd /path/to/your/script && python redash_to_slack.py

# Or weekly on Mondays:
0 9 * * 1 cd /path/to/your/script && python redash_to_slack.py
```

### Option C: Run Manually
Just double-click the script or run `python redash_to_slack.py` whenever you want reports.

## Troubleshooting

### ❌ "Failed to refresh query"
- Check your Redash URL and API key
- Make sure the query ID exists
- Verify you have permission to run the query

### ❌ "Failed to send to Slack"
- Check your webhook URL
- Make sure the Slack app is installed in your workspace

### ❌ "No module named 'requests'"
```bash
pip install requests
```

### ❌ Query takes too long
- Increase the timeout in line 34: `for attempt in range(60):` (60 seconds)
- Or optimize your SQL query in Redash

## 🎉 You're Done!

Your script will now:
- ✅ Run your Redash queries
- ✅ Format the results nicely  
- ✅ Send them to Slack with a preview
- ✅ Include links back to Redash
- ✅ Run automatically on schedule

**Next Steps:**
- Add more queries to the list
- Customize the Slack message format
- Set up different schedules for different reports