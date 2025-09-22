# Updated Redash Query - Date Parameter Changes

## What Changed

I've updated your `date_parameters` CTE to automatically calculate the date range instead of using manual parameters:

### Before (Manual Parameters):
```sql
WITH date_parameters AS (
    SELECT
        CAST('{{Month Start}}' AS DATE) AS report_start_date,
        CAST('{{End Date}}' AS DATE) AS report_end_date
),
```

### After (Dynamic Calculation):
```sql
WITH date_parameters AS (
    SELECT
        -- Start date: First day of current month
        DATE_FORMAT(CURDATE(), '%Y-%m-01') AS report_start_date,
        
        -- End date: Most recent Sunday
        -- If today is Sunday (DAYOFWEEK = 1), use the previous Sunday
        -- Otherwise, calculate days back to most recent Sunday
        CASE 
            WHEN DAYOFWEEK(CURDATE()) = 1 THEN -- Today is Sunday
                DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            ELSE 
                DATE_SUB(CURDATE(), INTERVAL (DAYOFWEEK(CURDATE()) - 1) DAY)
        END AS report_end_date
),
```

## How It Works

### MySQL Date Functions Used:
- `CURDATE()` - Gets current date
- `DATE_FORMAT(CURDATE(), '%Y-%m-01')` - First day of current month
- `DAYOFWEEK(CURDATE())` - Day of week (1=Sunday, 2=Monday, etc.)
- `DATE_SUB()` - Subtracts intervals from dates

### Logic for Most Recent Sunday:
- **If today is Sunday (DAYOFWEEK = 1)**: Go back 7 days to previous Sunday
- **If today is any other day**: Calculate days back to most recent Sunday using `(DAYOFWEEK(CURDATE()) - 1)`

### Examples:
| Today's Date | Day of Week | DAYOFWEEK() | Days to Subtract | Result |
|--------------|-------------|-------------|------------------|--------|
| 2025-09-22 | Monday | 2 | 2-1 = 1 | 2025-09-21 (Sunday) |
| 2025-09-29 | Monday | 2 | 2-1 = 1 | 2025-09-28 (Sunday) |
| 2025-09-21 | Sunday | 1 | 7 days | 2025-09-14 (Previous Sunday) |

## Benefits

1. **Automatic Updates**: Query runs with current date logic every time
2. **No Manual Parameters**: Eliminates need to update `{{Month Start}}` and `{{End Date}}` parameters
3. **Consistent Logic**: Always pulls from first of month to most recent Sunday
4. **Perfect for Monday Reports**: Since your completeness check runs on Monday, it will always capture through the previous Sunday

## Usage

Simply replace your existing query with the updated version. The rest of your query logic remains exactly the same - only the date parameter calculation has changed.