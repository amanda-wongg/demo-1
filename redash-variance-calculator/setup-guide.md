# Variance Calculator Setup Guide

## What This Does

This script will:
- ✅ Fetch data from your Redash queries for any date range
- ✅ Calculate variance, standard deviation, coefficient of variation
- ✅ Detect outliers and trends
- ✅ Send intelligent alerts to Slack when variance exceeds thresholds
- ✅ Work even if you can't connect Redash directly to external tools

## Quick Setup (10 minutes)

### Step 1: Install Python Requirements
```bash
pip install requests numpy
```

### Step 2: Configure the Script
Edit `variance_analyzer.py` and change these lines:

```python
# Line 15-17: Your credentials
REDASH_URL = "https://your-redash-instance.com"     # ← Your Redash URL
REDASH_API_KEY = "your-api-key-here"                # ← Your Redash API key  
SLACK_WEBHOOK_URL = "https://hooks.slack.com/..."   # ← Your Slack webhook
```

### Step 3: Configure Your Queries
In the `main()` function, update the `analysis_jobs` list:

```python
analysis_jobs = [
    {
        "query_id": 123,                    # ← Your Redash query ID
        "query_name": "Daily Sales Variance",
        "value_column": "sales_amount",     # ← Column with numbers to analyze
        "date_column": "sale_date",         # ← Date column (optional)
        "thresholds": {
            "high_cv_threshold": 25.0,      # Alert if variance > 25%
            "outlier_threshold": 3,         # Alert if > 3 outliers
            "variance_threshold": 500       # Alert if raw variance > 500
        }
    }
]
```

### Step 4: Update Your Redash Query
Your Redash query needs to accept date parameters. Add this to your SQL:

```sql
SELECT 
    date_column,
    value_column,
    -- other columns
FROM your_table 
WHERE date_column BETWEEN '{{start_date}}' AND '{{end_date}}'
ORDER BY date_column
```

### Step 5: Run It
```bash
python variance_analyzer.py
```

## What You'll Get in Slack

```
⚠️ **Variance Alert: Daily Sales Variance**
📅 Period: 2024-01-01 to 2024-01-31

📈 **Key Statistics:**
• Sample Size: 1,250 data points
• Average: 15,432.50
• Variance: 2,450,678.90
• Std Deviation: 1,565.45
• Range: 8,234.00 - 28,945.00

🎯 **Risk Assessment:**
• Variability: 32.5% CV ⚠️
• Trend: Increasing
• Outliers: 8 detected

🚨 **Alerts:**
• High variability: 32.5% CV
• 8 outliers detected
• Trend detected: increasing

🔍 **Sample Outliers:** 28945.0, 28234.5, 27890.2
```

## Advanced Usage

### Custom Date Ranges
You can modify the date range in the script:

```python
# Last 7 days
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

# Specific date range
start_date = "2024-01-01"
end_date = "2024-01-31"

# Last month
today = datetime.now()
start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d')
end_date = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
```

### Multiple Metrics
Analyze different columns from the same query:

```python
# Run the same query but analyze different columns
analyzer.analyze_and_alert(123, "Revenue Analysis - Sales", "sales_amount", start_date, end_date)
analyzer.analyze_and_alert(123, "Revenue Analysis - Profit", "profit_amount", start_date, end_date)
```

### Automation
Set up a cron job to run daily:

```bash
# Run every day at 9 AM
0 9 * * * cd /path/to/script && python variance_analyzer.py

# Run every Monday for weekly variance
0 9 * * 1 cd /path/to/script && python variance_analyzer.py
```

## Troubleshooting

### ❌ "Failed to refresh query"
- Check your Redash API key
- Make sure the query ID exists
- Verify your query accepts `start_date` and `end_date` parameters

### ❌ "Insufficient data for variance calculation"
- Check your date range isn't too narrow
- Verify the `value_column` name matches your query results
- Make sure your query returns numeric data

### ❌ "Failed to send to Slack"
- Verify your Slack webhook URL
- Test the webhook manually: `curl -X POST -H 'Content-type: application/json' --data '{"text":"Test"}' YOUR_WEBHOOK_URL`

### 🔧 Debug Mode
Add this to see what data you're getting:

```python
# After line "data = self.run_query_with_params(query_id, parameters)"
print(f"Sample data: {data[:3]}")  # Show first 3 rows
print(f"Columns available: {list(data[0].keys()) if data else 'No data'}")
```

## Benefits Over Simple Solutions

✅ **Intelligent Analysis**: Not just data forwarding - actual variance calculations
✅ **Flexible Thresholds**: Set custom alert levels for different metrics  
✅ **Trend Detection**: Identifies if variance is increasing/decreasing
✅ **Outlier Detection**: Finds unusual data points automatically
✅ **Date Range Flexibility**: Analyze any time period
✅ **Multiple Queries**: Analyze different metrics with one script
✅ **Rich Alerts**: Context-aware notifications, not just raw data