# Setup Guide: Cash Completeness Monitor

This guide walks you through setting up the Cash Completeness Monitor from scratch.

## Prerequisites

- Python 3.9 or higher
- Access to your Redash instance with API key
- Slack workspace with bot creation permissions
- AWS/GCP account (if deploying to cloud)

## Step 1: Environment Setup

### Local Development
```bash
# Create project directory
mkdir cash_completeness_monitor
cd cash_completeness_monitor

# Install Python dependencies
pip install -r requirements.txt

# Make CLI executable
chmod +x cli.py
```

### Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Redash Configuration

### 1. Get API Key
1. Log into your Redash instance
2. Go to Settings → Account → API Key
3. Copy the API key

### 2. Identify Query IDs
1. Navigate to your existing cash completeness queries
2. Note the query ID from the URL (e.g., `/queries/123` → ID is `123`)
3. Ensure queries accept `start_date` and `end_date` parameters

### 3. Query Format Requirements
Your queries should return columns:
- `account`: Account identifier
- `delta_amount`: Variance amount (positive or negative)
- `currency`: Currency code (optional, defaults to USD)

Example query:
```sql
SELECT 
    account_name as account,
    (expected_balance - actual_balance) as delta_amount,
    'USD' as currency,
    expected_balance,
    actual_balance
FROM cash_balance_comparison 
WHERE abs(expected_balance - actual_balance) > {{threshold|100}}
  AND date >= '{{start_date}}'
  AND date <= '{{end_date}}'
```

## Step 3: Slack Bot Setup

### 1. Create Slack App
1. Go to https://api.slack.com/apps
2. Click "Create New App"
3. Choose "From scratch"
4. Name: "Cash Completeness Monitor"
5. Select your workspace

### 2. Configure Bot Permissions
1. Go to "OAuth & Permissions"
2. Add these Bot Token Scopes:
   - `chat:write`
   - `chat:write.public`
   - `channels:read`
   - `groups:read`

### 3. Install App
1. Click "Install to Workspace"
2. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### 4. Invite Bot to Channel
1. Go to your target Slack channel (e.g., `#monthly-reconciliations`)
2. Type `/invite @Cash Completeness Monitor`
3. Or add via channel settings

## Step 4: Configuration File

### 1. Create Configuration
```bash
python cli.py create-config --output config.json
```

### 2. Edit Configuration
Open `config.json` and update with your values:

```json
{
  "redash_base_url": "https://your-company.redash.com",
  "redash_api_key": "your-actual-api-key",
  "redash_queries": [
    {
      "query_id": 123,
      "name": "BAI2 Balance Check",
      "description": "Daily BAI2 balance reconciliation"
    }
  ],
  "slack_bot_token": "xoxb-your-actual-bot-token",
  "slack_channel": "#monthly-reconciliations",
  "significance_threshold": 100.0
}
```

### 3. Validate Configuration
```bash
python cli.py validate --config config.json
```

## Step 5: Testing

### 1. Test Connections
```bash
python cli.py test --config config.json
```
This should show:
- ✅ Redash connection successful
- ✅ Slack connection successful
- ✅ All configured queries accessible

### 2. Test Query Execution
```bash
python cli.py run --config config.json
```
This performs a full check cycle and shows results.

### 3. Test Slack Alerts
```bash
python cli.py test-alert --config config.json
```
This sends a test variance alert to your Slack channel.

## Step 6: Deployment

Choose your deployment method:

### Option A: AWS Lambda (Recommended for AWS users)

```bash
cd deploy
./aws_deploy.sh
```

Set environment variables:
```bash
aws lambda update-function-configuration \
  --function-name cash-completeness-monitor \
  --environment Variables='{
    "REDASH_BASE_URL":"https://your-redash.com",
    "REDASH_API_KEY":"your-key",
    "SLACK_BOT_TOKEN":"xoxb-your-token",
    "SLACK_CHANNEL":"#monthly-reconciliations",
    "REDASH_QUERIES":"[{\"query_id\":123,\"name\":\"BAI2 Check\"}]"
  }'
```

### Option B: Google Cloud Functions

```bash
cd deploy
./gcp_deploy.sh
```

### Option C: Local Cron Job

Add to crontab:
```bash
crontab -e
# Add this line for daily execution at 7 AM:
0 7 * * * cd /path/to/cash_completeness_monitor && python main.py >> /var/log/cash-monitor.log 2>&1
```

### Option D: Docker

```bash
docker build -t cash-monitor .
docker run -d \
  -e REDASH_BASE_URL="https://your-redash.com" \
  -e REDASH_API_KEY="your-key" \
  -e SLACK_BOT_TOKEN="xoxb-your-token" \
  -e SLACK_CHANNEL="#monthly-reconciliations" \
  -e REDASH_QUERIES='[{"query_id":123,"name":"Test"}]' \
  --name cash-monitor \
  cash-monitor
```

## Step 7: Monitoring Setup

### 1. Set Up Log Monitoring
- AWS: CloudWatch Logs
- GCP: Cloud Logging
- Local: Log files in `/var/log/`

### 2. Health Check Endpoint (Optional)
Create a simple health check:
```bash
# Test daily (adjust for your deployment)
curl -X POST https://your-function-url/health
```

### 3. Alert Monitoring
Monitor for:
- Function execution failures
- API connection issues
- Missing daily executions

## Step 8: Initial Run & Calibration

### 1. First Execution
The first run will detect all current variances as "new". This is expected.

### 2. Calibrate Known Variances
After the first run, review the alerts and identify any expected/ongoing variances:

```bash
# List detected variances
python cli.py list-variances

# Remove expected variances (they won't alert again unless amount changes)
python cli.py remove-variance VARIANCE_ID
```

### 3. Adjust Threshold
If too many small variances are detected:
```json
{
  "significance_threshold": 500.0
}
```

## Step 9: Team Onboarding

### 1. Document Process
- Share this setup guide with your team
- Document your specific query configurations
- Create runbook for common operations

### 2. Train Team Members
Show team members how to:
- Interpret Slack alerts
- Use CLI for manual checks
- Remove false positive variances

### 3. Establish Procedures
Define procedures for:
- Investigating new variances
- Managing known ongoing issues
- System maintenance and updates

## Troubleshooting Common Setup Issues

### "Configuration validation failed"
- Check all required fields are present
- Verify JSON syntax is correct
- Ensure query IDs are numbers, not strings

### "Redash connection failed"
- Verify base URL is correct (include https://)
- Check API key has proper permissions
- Test API key in Redash interface

### "Slack connection failed"
- Verify bot token starts with `xoxb-`
- Check bot is installed in workspace
- Ensure bot has `chat:write` permission

### "Query execution failed"
- Verify query ID exists and is accessible
- Check query accepts `start_date` and `end_date` parameters
- Test query manually in Redash with sample dates

### "No variances detected"
- Check significance threshold setting
- Verify query returns expected data format
- Run query manually to see raw results

## Next Steps

After successful setup:

1. **Monitor for a week** to ensure stable operation
2. **Fine-tune thresholds** based on false positive rates
3. **Add additional queries** as needed
4. **Set up automated backups** of state file
5. **Document any customizations** for your environment

## Support

For issues:
1. Check the troubleshooting section
2. Review system logs
3. Use CLI diagnostic commands
4. Test individual components

Remember: The system is designed to be "silent when all is well" - no news is good news!