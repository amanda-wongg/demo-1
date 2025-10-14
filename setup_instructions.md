# Variance Alert System Setup Instructions

This system solves the problem of Redash alerts triggering on known historical variances by implementing a smart filtering layer that excludes approved historical variances before alerting.

## 🎯 Problem Solved

**Original Issue**: Redash can only set a simple threshold (e.g., variance > $0.00), but this triggers alerts for known historical variances that are already approved.

**Solution**: Pre-filter variances to exclude known historical ones, then use Redash's simple threshold on the filtered results.

## 📋 Setup Options

### Option 1: Python-Based Processing (Recommended)

Use the `variance_alert_system.py` to process variances before they reach Redash.

#### Prerequisites
```bash
pip install pandas sqlite3 requests
```

#### Setup Steps

1. **Initialize the System**
```python
from variance_alert_system import VarianceAlertSystem

# Initialize with your Slack webhook
alert_system = VarianceAlertSystem(
    slack_webhook_url="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
)
```

2. **Add Historical Exclusions**
```python
# Add known historical variances that should not trigger alerts
alert_system.add_historical_exclusion(
    date="2024-01-15",
    amount=500.00,
    description="Monthly reconciliation adjustment",
    category="reconciliation", 
    approved_by="finance_team"
)
```

3. **Add Variance Patterns**
```python
# Automatically exclude small reconciliation variances
alert_system.historical_manager.add_variance_pattern(
    pattern_name="small_reconciliation",
    category="reconciliation",
    amount_threshold=100.00
)
```

4. **Process Your Variance Data**
```python
# Your variance data (from database, API, etc.)
variance_data = [
    {
        "date": "2024-10-14",
        "amount": 2500.00,
        "description": "Unexpected expense variance",
        "category": "expenses"
    }
    # ... more variances
]

# Process and get only variances that should trigger alerts
alerts = alert_system.process_variance_data(variance_data)
```

### Option 2: SQL-Based Filtering in Redash

Use the provided `redash_integration.sql` query template.

#### Setup Steps

1. **Customize the Query**
   - Replace `your_variance_table` with your actual table name
   - Update the `historical_exclusions` CTE with your known variances
   - Modify `variance_patterns` for your business rules

2. **Create Redash Query**
   - Copy the SQL from `redash_integration.sql`
   - Create a new query in Redash
   - Add a parameter `threshold` (default: 0)

3. **Configure Redash Alert**
   - Condition: "Query returns results"
   - Threshold: Leave at default since filtering is in the query
   - Destination: Your Slack channel

## 🔧 Configuration Examples

### Adding Historical Variances

```python
# One-time historical variances
alert_system.add_historical_exclusion(
    date="2024-01-31",
    amount=1200.00,
    description="Year-end accrual adjustment",
    category="accruals",
    approved_by="controller"
)

# Recurring monthly variances
for month in range(1, 13):
    alert_system.add_historical_exclusion(
        date=f"2024-{month:02d}-15",
        amount=500.00,
        description="Monthly reconciliation adjustment",
        category="reconciliation",
        approved_by="finance_team"
    )
```

### Setting Up Patterns

```python
# Exclude small reconciliation differences
alert_system.historical_manager.add_variance_pattern(
    pattern_name="small_reconciliation",
    category="reconciliation",
    amount_threshold=100.00
)

# Exclude accrual adjustments under $50
alert_system.historical_manager.add_variance_pattern(
    pattern_name="small_accruals", 
    category="accruals",
    amount_threshold=50.00
)

# Exclude anything with "adjustment" in description under $200
alert_system.historical_manager.add_variance_pattern(
    pattern_name="general_adjustments",
    amount_threshold=200.00,
    description_pattern="adjustment"
)
```

## 🚀 Integration Workflows

### Workflow 1: Batch Processing

```python
# Run this as a scheduled job (cron, Airflow, etc.)
def daily_variance_check():
    # Get today's variances from your data source
    variances = get_variances_from_database(date.today())
    
    # Process through the alert system
    alerts = alert_system.process_variance_data(variances)
    
    # Log results
    print(f"Processed {len(variances)} variances, {len(alerts)} alerts sent")

# Schedule this to run daily
```

### Workflow 2: Real-time Processing

```python
# Integrate into your existing variance calculation pipeline
def process_new_variance(variance_data):
    variance = VarianceRecord(
        date=variance_data['date'],
        amount=variance_data['amount'], 
        description=variance_data['description'],
        category=variance_data['category']
    )
    
    should_alert, reason = alert_system.processor.process_variance(variance)
    
    if should_alert:
        # Send to Redash or directly to Slack
        alert_system.redash.send_slack_alert(variance, reason)
    
    return should_alert
```

### Workflow 3: Redash Query Enhancement

Replace your existing Redash variance query with the filtered version:

```sql
-- Instead of:
SELECT * FROM variances WHERE variance_amount > 0

-- Use:
-- [The full query from redash_integration.sql]
```

## 📊 Monitoring and Management

### View Excluded Variances

```python
# Check what variances are being excluded
conn = sqlite3.connect("variance_history.db")
excluded_variances = pd.read_sql_query('''
    SELECT date, amount, description, category, approved_by
    FROM historical_variances 
    WHERE variance_type = 'approved_historical'
    ORDER BY date DESC
''', conn)
print(excluded_variances)
```

### Update Exclusion Rules

```python
# Add new exclusion
alert_system.add_historical_exclusion(
    date="2024-10-15",
    amount=800.00,
    description="New approved variance",
    category="special_items",
    approved_by="cfo"
)

# Add new pattern
alert_system.historical_manager.add_variance_pattern(
    pattern_name="quarterly_adjustments",
    description_pattern="quarterly",
    amount_threshold=300.00
)
```

## 🎛️ Redash Alert Configuration

1. **Query Setup**:
   - Use the filtered SQL query
   - Set threshold parameter to 0
   - Query should return only unexpected variances

2. **Alert Condition**: 
   - "Query returns results" (not threshold-based)
   - This triggers when unexpected variances are found

3. **Notification**:
   - Configure Slack destination
   - Customize message template to include variance details

## 🔍 Troubleshooting

### Common Issues

1. **Too Many Alerts**: Add more historical exclusions or lower pattern thresholds
2. **Missing Alerts**: Check if variance is being incorrectly excluded
3. **Database Errors**: Ensure SQLite database has proper permissions

### Debug Mode

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check processing for specific variance
variance = VarianceRecord(...)
should_alert, reason = alert_system.processor.process_variance(variance)
print(f"Alert: {should_alert}, Reason: {reason}")
```

## 📈 Benefits

- ✅ **Eliminates False Positives**: No more alerts for known historical variances
- ✅ **Maintains Sensitivity**: Still catches new, unexpected variances  
- ✅ **Flexible Rules**: Easy to add new exclusions and patterns
- ✅ **Audit Trail**: All exclusions are tracked with approval metadata
- ✅ **Redash Compatible**: Works with existing Redash infrastructure
- ✅ **Scalable**: Handles large volumes of variance data efficiently

This solution transforms your simple Redash threshold into an intelligent alerting system that understands your business context and only alerts on truly unexpected variances.