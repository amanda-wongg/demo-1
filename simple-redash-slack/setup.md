# Simple Redash → Slack Integration

## 5-Minute Setup

### Step 1: Get Slack Webhook URL
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name it "Redash Bot", select your workspace
4. Go to "Incoming Webhooks" → Toggle "On"
5. Click "Add New Webhook to Workspace"
6. Choose your channel → "Allow"
7. Copy the webhook URL (starts with `https://hooks.slack.com/`)

### Step 2: Get Redash API Key
1. Log into your Redash instance
2. Click your profile (top right) → "Settings"
3. Go to "API Key" tab
4. Copy your API key

### Step 3: Configure the Script
Edit `webhook.py` and change these lines:
```python
REDASH_URL = "https://your-redash-instance.com"  # Your Redash URL
REDASH_API_KEY = "your-api-key-here"             # Your API key
SLACK_WEBHOOK_URL = "https://hooks.slack.com..." # Your webhook URL
```

### Step 4: Add Your Queries
In the `queries` list, add your Redash query IDs:
```python
queries = [
    {"id": 123, "name": "Daily Sales Report"},    # Replace 123 with real query ID
    {"id": 456, "name": "User Signups"},          # Add more as needed
]
```

### Step 5: Run It
```bash
python webhook.py
```

## Automation Options

### Option A: Cron Job (Linux/Mac)
```bash
# Run every day at 9 AM
0 9 * * * cd /path/to/script && python webhook.py

# Run every Monday at 9 AM  
0 9 * * 1 cd /path/to/script && python webhook.py
```

### Option B: Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily, weekly, etc.)
4. Action: Start Program → `python.exe`
5. Arguments: `/path/to/webhook.py`

### Option C: GitHub Actions (Free)
Create `.github/workflows/redash-slack.yml`:
```yaml
name: Redash to Slack
on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM UTC
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install requests
      - run: python webhook.py
```

## That's it! 
No servers, no databases, no complexity. Just queries → Slack.