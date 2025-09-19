# Cash Completeness Monitor 🤖

**Real-Time Automation of Customer Cash Completeness Checks**

This system transforms the manual, weekly Customer Cash Completeness Check process into an automated, daily monitoring system with intelligent variance detection and management-by-exception alerting.

## 🎯 Key Benefits

- **Proactive Detection**: Reduces time-to-detection from up to 7 days to less than 24 hours
- **Management by Exception**: Only alerts on new variances, eliminating noise
- **Automated Operations**: Eliminates 15-30 minutes of manual effort per check
- **Intelligent Filtering**: Tracks known variances to prevent duplicate alerts
- **Rich Alerting**: Formatted Slack notifications with actionable information

## 🏗️ Architecture

The system consists of several key components:

- **Main Monitor (`main.py`)**: Core monitoring logic and orchestration
- **Redash Client (`redash_client.py`)**: Handles query execution and result retrieval
- **Slack Client (`slack_client.py`)**: Manages alert formatting and delivery
- **State Manager (`state_manager.py`)**: Persistent storage for known variances
- **Configuration (`config.py`)**: Centralized configuration management
- **CLI (`cli.py`)**: Command-line utilities for testing and management

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or create the project directory
cd cash_completeness_monitor

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a configuration file:

```bash
python cli.py create-config --output config.json
```

Edit `config.json` with your actual values:

```json
{
  "redash_base_url": "https://your-redash-instance.com",
  "redash_api_key": "your-redash-api-key",
  "slack_bot_token": "xoxb-your-slack-bot-token",
  "slack_channel": "#monthly-reconciliations",
  "redash_queries": [
    {
      "query_id": 123,
      "name": "BAI2 Bank Balance Check",
      "description": "Compares BAI2 reported balances with internal records"
    }
  ],
  "significance_threshold": 100.0,
  "state_storage_path": "state.json"
}
```

### 3. Test Connections

```bash
python cli.py test --config config.json
```

### 4. Run Manual Check

```bash
python cli.py run --config config.json
```

## 📋 Configuration Reference

### Required Settings

| Setting | Description | Example |
|---------|-------------|---------|
| `redash_base_url` | Base URL of your Redash instance | `https://redash.company.com` |
| `redash_api_key` | Redash API key for authentication | `abc123...` |
| `slack_bot_token` | Slack bot token | `xoxb-...` |
| `slack_channel` | Slack channel for alerts | `#reconciliations` |
| `redash_queries` | Array of query configurations | See below |

### Query Configuration

Each query in `redash_queries` should have:

```json
{
  "query_id": 123,
  "name": "Descriptive Name",
  "description": "What this query checks",
  "additional_params": {
    "account_type": "operations"
  }
}
```

### Optional Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `significance_threshold` | 100.0 | Minimum variance amount to consider |
| `state_storage_path` | `state.json` | Path to state storage file |
| `log_level` | `INFO` | Logging level |
| `query_timeout` | 300 | Query execution timeout (seconds) |
| `alert_on_system_errors` | true | Send alerts for system errors |

## 🔧 CLI Commands

The CLI provides various utilities for managing the system:

### Basic Operations
```bash
# Run a manual check
python cli.py run

# Test all connections
python cli.py test

# Show system status
python cli.py status

# Validate configuration
python cli.py validate
```

### Variance Management
```bash
# List all known variances
python cli.py list-variances

# Remove a specific variance (will re-alert if seen again)
python cli.py remove-variance VARIANCE_ID

# Clean up old variances (older than 90 days)
python cli.py cleanup --days 90
```

### Testing
```bash
# Send a test alert to Slack
python cli.py test-alert

# Create sample configuration
python cli.py create-config --output sample-config.json
```

## 🚀 Deployment Options

### AWS Lambda

Deploy to AWS Lambda with CloudWatch Events scheduling:

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
    "SLACK_CHANNEL":"#reconciliations",
    "REDASH_QUERIES":"[{\"query_id\":123,\"name\":\"Test Query\"}]"
  }'
```

### Google Cloud Functions

Deploy to Google Cloud Functions with Cloud Scheduler:

```bash
cd deploy
./gcp_deploy.sh
```

Set environment variables:
```bash
gcloud functions deploy cash-completeness-monitor \
  --update-env-vars REDASH_BASE_URL=https://your-redash.com,REDASH_API_KEY=your-key,SLACK_BOT_TOKEN=xoxb-your-token,SLACK_CHANNEL=#reconciliations
```

### Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t cash-monitor .
docker run -e REDASH_BASE_URL=... -e REDASH_API_KEY=... cash-monitor
```

### Local Cron

Add to crontab for daily execution at 7 AM:
```bash
0 7 * * * cd /path/to/cash_completeness_monitor && python main.py
```

## 📊 Expected Query Format

Your Redash queries should return data in this format:

| Column | Type | Description |
|--------|------|-------------|
| `account` | String | Account identifier |
| `delta_amount` | Number | Variance amount |
| `currency` | String | Currency code (optional, defaults to USD) |
| Additional columns | Any | Stored in raw_data for reference |

Example query result:
```sql
SELECT 
    account_name as account,
    (expected_balance - actual_balance) as delta_amount,
    'USD' as currency,
    expected_balance,
    actual_balance,
    last_updated
FROM cash_balance_comparison 
WHERE abs(expected_balance - actual_balance) > 100
  AND date >= '{{start_date}}'
  AND date <= '{{end_date}}'
```

## 🔍 How It Works

### Daily Execution Flow

1. **Trigger**: System runs daily at 7 AM (configurable)
2. **Query Execution**: Executes all configured Redash queries for the last 24 hours
3. **Variance Detection**: Parses results to identify cash variances
4. **State Comparison**: Compares against known variances to identify new ones
5. **Alert Generation**: Sends Slack alerts only for new variances
6. **State Update**: Updates the known variances database

### Variance Identification

Each variance gets a unique ID based on:
- Check type (query name)
- Account
- Delta amount
- Currency

This ensures the same variance isn't reported multiple times.

### Management by Exception

The system implements "management by exception" by:
- Only alerting on NEW variances
- Maintaining silence when no new issues are found
- Tracking known variances to prevent duplicate alerts
- Providing rich context in alerts for immediate action

## 📈 Monitoring & Metrics

### System Metrics

The state manager tracks:
- Total checks performed
- Total variances detected
- Total alerts sent
- Known variance count

View metrics:
```bash
python cli.py status
```

### Logs

Monitor system logs for:
- Daily execution results
- API connection issues
- Query execution problems
- Alert delivery status

### Health Checks

The system provides several health check mechanisms:
- Connection testing (`python cli.py test`)
- Configuration validation (`python cli.py validate`)
- Manual execution (`python cli.py run`)

## 🛠️ Troubleshooting

### Common Issues

**"Query execution failed"**
- Check Redash API key and permissions
- Verify query ID exists and is accessible
- Check query parameters and date formatting

**"Slack message failed"**
- Verify Slack bot token and permissions
- Check channel exists and bot is invited
- Validate channel name format (#channel-name)

**"No variances detected"**
- Verify query returns expected data format
- Check significance threshold setting
- Review date range parameters

### Debug Mode

Enable verbose logging:
```bash
python cli.py run --verbose
```

### State Management Issues

Reset state (will cause re-alerting):
```bash
rm state.json
```

Clean up old variances:
```bash
python cli.py cleanup --days 30
```

## 🔒 Security Considerations

- Store API keys and tokens as environment variables
- Use least-privilege access for Redash and Slack
- Regularly rotate API keys
- Monitor access logs
- Consider encrypting the state file for sensitive environments

## 📚 API Reference

### Environment Variables

When deploying to serverless environments, you can use environment variables instead of a config file:

| Variable | Required | Description |
|----------|----------|-------------|
| `REDASH_BASE_URL` | Yes | Redash instance URL |
| `REDASH_API_KEY` | Yes | Redash API key |
| `SLACK_BOT_TOKEN` | Yes | Slack bot token |
| `SLACK_CHANNEL` | Yes | Slack channel |
| `REDASH_QUERIES` | Yes | JSON string of query configs |
| `SIGNIFICANCE_THRESHOLD` | No | Minimum variance amount |
| `STATE_STORAGE_PATH` | No | State file path |
| `LOG_LEVEL` | No | Logging level |

### State File Format

The state file (`state.json`) contains:
```json
{
  "version": "1.0",
  "created_at": "2025-09-19T...",
  "last_updated": "2025-09-19T...",
  "last_check_time": "2025-09-19T...",
  "known_variances": {
    "variance_id": {
      "check_type": "...",
      "account": "...",
      "delta_amount": 123.45,
      "first_detected": "...",
      "times_seen": 1
    }
  },
  "system_metrics": {
    "total_checks_performed": 10,
    "total_variances_detected": 5,
    "total_alerts_sent": 3
  }
}
```

## 🤝 Contributing

This system was designed to be easily extensible. Key areas for enhancement:

- Additional data source integrations
- Enhanced alerting channels (email, Teams, etc.)
- More sophisticated variance analysis
- Dashboard/reporting interface
- Advanced scheduling options

## 📄 License

This project is provided as-is for internal use. Modify and adapt as needed for your environment.

---

**Questions?** Check the troubleshooting section or run `python cli.py --help` for additional options.