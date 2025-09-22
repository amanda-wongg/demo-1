# 📊 Bank Account Variance Monitor

An automated system that runs every Monday to check for bank account variances and sends Slack alerts when discrepancies are detected.

## 🎯 Overview

This system monitors your bank account reconciliation data and automatically:
- Queries variance data from the first of the month to yesterday
- Identifies records where the variance column is not equal to zero
- Sends detailed Slack notifications with variance information
- Logs all activities for audit and troubleshooting

## 📋 Features

- **Automated Scheduling**: Runs every Monday at 9:00 AM via cron job
- **Smart Date Ranges**: Automatically calculates first-of-month to yesterday
- **Detailed Alerts**: Rich Slack messages with variance breakdowns
- **Error Handling**: Comprehensive error handling and logging
- **Test Suite**: Built-in testing tools for validation
- **Flexible Database Support**: Works with PostgreSQL, MySQL, SQL Server, Oracle

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Make setup script executable
chmod +x setup_cron.sh

# Run the setup script
./setup_cron.sh
```

### 2. Configure Environment Variables

Copy and edit the environment file:
```bash
cp .env.example .env
nano .env
```

Required variables:
```bash
DATABASE_CONNECTION_STRING=your_database_connection_string
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#finance-alerts  # Optional
```

### 3. Test the Setup

```bash
# Run the test suite
python3 test_variance_monitor.py

# Test manually (optional)
python3 variance_monitor.py
```

## 🔧 Configuration

### Database Connection Strings

Choose the appropriate format for your database:

**PostgreSQL:**
```
postgresql://username:password@host:port/database
```

**MySQL:**
```
mysql+pymysql://username:password@host:port/database
```

**SQL Server:**
```
mssql+pyodbc://username:password@host:port/database?driver=ODBC+Driver+17+for+SQL+Server
```

**Oracle:**
```
oracle+cx_oracle://username:password@host:port/database
```

### Slack Webhook Setup

1. Go to your Slack workspace settings
2. Create a new app or use existing one
3. Enable "Incoming Webhooks"
4. Create a webhook for your desired channel
5. Copy the webhook URL to your `.env` file

## 📊 Sample Query Structure

The system expects your database table to have these columns:
- `bank_account`: Account identifier
- `reconciled_payment_records`: Payment records amount
- `bt_date_1`, `bt_date_2`: Balance dates
- `bt_balance_1`, `bt_balance_2`: Balance amounts
- `movement`: Account movement
- `difference`: Calculated difference
- `unreconciled_bt_credit`: Unreconciled credits
- `unreconciled_bt_debit`: Unreconciled debits
- `unreconciled_bt_absolute_total`: Total unreconciled
- `variance`: The variance amount (alerts when ≠ 0)

**Important:** You'll need to update the SQL query in `variance_monitor.py` to match your actual table name and structure.

## 🗓️ Scheduling

The cron job runs every Monday at 9:00 AM:
```bash
0 9 * * 1 cd /workspace && python3 variance_monitor.py >> variance_monitor.log 2>&1
```

### Managing the Cron Job

```bash
# View current cron jobs
crontab -l

# Edit cron jobs manually
crontab -e

# Remove the variance monitor cron job
crontab -l | grep -v "variance_monitor.py" | crontab -
```

## 📱 Slack Notifications

### No Variances Found
```
✅ No variances detected for period 2025-09-01 to 2025-09-21
All bank account reconciliations are balanced.
```

### Variances Detected
```
🚨 VARIANCE ALERT - 2025-09-01 to 2025-09-21

Summary:
• 2 variance records found
• 2 accounts affected  
• Total absolute variance: $10,056.09

🔴 Chase operations-3
• Variance: $-10,000.00
• Movement: $-318,546,285.31
• Difference: $15,169,668.37
• Period: 2025-08-31 to 2025-09-21

🟡 PNC operations-16
• Variance: $-56.09
• Movement: $0.00
• Difference: $-56.09
• Period: 2025-08-31 to 2025-09-21
```

## 🧪 Testing

### Run Test Suite
```bash
python3 test_variance_monitor.py
```

The test suite validates:
- Configuration completeness
- Database connectivity
- Date range calculations
- Slack message formatting
- Full workflow execution

### Manual Testing
```bash
# Test the main script
python3 variance_monitor.py

# Check logs
tail -f variance_monitor.log
```

## 📁 File Structure

```
/workspace/
├── variance_monitor.py          # Main monitoring script
├── test_variance_monitor.py     # Test suite
├── setup_cron.sh               # Setup and installation script
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .env                       # Your configuration (create this)
├── variance_monitor.log       # Log file (created automatically)
└── VARIANCE_MONITOR_README.md # This documentation
```

## 🔍 Troubleshooting

### Common Issues

**1. Database Connection Fails**
- Verify connection string format
- Check database credentials
- Ensure database server is accessible
- Install appropriate database driver

**2. Slack Notifications Not Sent**
- Verify webhook URL is correct
- Check Slack app permissions
- Ensure webhook is enabled
- Test webhook with curl:
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test message"}' \
  YOUR_WEBHOOK_URL
```

**3. Cron Job Not Running**
- Check if cron service is running: `systemctl status cron`
- Verify cron job exists: `crontab -l`
- Check system logs: `grep CRON /var/log/syslog`
- Ensure script has execute permissions

**4. Python Dependencies Missing**
```bash
# Install dependencies
pip3 install -r requirements.txt

# Or install individually
pip3 install requests pandas sqlalchemy python-dotenv
```

### Log Analysis

Monitor the log file for issues:
```bash
# View recent logs
tail -n 50 variance_monitor.log

# Follow logs in real-time
tail -f variance_monitor.log

# Search for errors
grep -i error variance_monitor.log
```

## 🔒 Security Considerations

- Store sensitive credentials in environment variables, not in code
- Use database users with minimal required permissions
- Regularly rotate API keys and database passwords
- Consider using secrets management systems for production
- Limit Slack webhook permissions to specific channels

## 📈 Monitoring & Maintenance

### Regular Tasks
- Monitor log files for errors
- Test Slack webhook periodically
- Verify database connectivity
- Review and update SQL queries as needed
- Keep Python dependencies updated

### Performance Optimization
- Add database indexes on date columns
- Consider query optimization for large datasets
- Implement query result caching if needed
- Monitor script execution time

## 🤝 Customization

### Modifying the SQL Query

Edit the `execute_variance_query` method in `variance_monitor.py`:

```python
def execute_variance_query(self, start_date: datetime.date, end_date: datetime.date) -> List[VarianceRecord]:
    query = """
    -- Replace this with your actual query
    SELECT 
        your_account_column as bank_account,
        your_variance_column as variance,
        -- ... other columns
    FROM your_table_name
    WHERE your_date_column >= :start_date 
    AND your_date_column <= :end_date
    AND your_variance_column != 0
    """
```

### Changing the Schedule

Edit the cron job timing:
```bash
crontab -e
```

Examples:
- Daily at 8 AM: `0 8 * * *`
- Weekdays at 9 AM: `0 9 * * 1-5`
- First Monday of month: `0 9 1-7 * 1`

### Custom Slack Formatting

Modify the `format_variance_message` method to customize Slack message appearance, add more details, or change the formatting.

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review log files for error details
3. Test individual components using the test suite
4. Verify configuration and permissions

---

*Last updated: September 22, 2025*