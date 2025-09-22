# Redash Date Parameter Query

## Overview
This SQL query creates a dynamic date range for Redash that pulls data from the **first day of the current month** to the **most recent Sunday**. This is designed for weekly completeness checks that run on Monday.

## How It Works

### Date Logic
- **Start Date**: Always the 1st day of the current month
- **End Date**: The most recent Sunday before today
  - If today is Sunday: Uses the previous Sunday (7 days ago)
  - If today is any other day: Calculates back to the most recent Sunday

### Examples
| Today's Date | Day of Week | Start Date | End Date | Explanation |
|--------------|-------------|------------|----------|-------------|
| 9/22/25 | Monday | 9/1/25 | 9/21/25 | Most recent Sunday was yesterday |
| 9/29/25 | Monday | 9/1/25 | 9/28/25 | Most recent Sunday was yesterday |
| 9/21/25 | Sunday | 9/1/25 | 9/14/25 | Since today is Sunday, use previous Sunday |

## Files Included

1. **`redash_production_query.sql`** - The main query to use in Redash
2. **`redash_date_logic_test.sql`** - Test queries to verify the date logic
3. **`redash_date_query.sql`** - Original detailed version with comments

## Usage in Redash

1. Copy the content from `redash_production_query.sql`
2. Replace the example section with your actual table and columns:
   ```sql
   -- Replace this part:
   FROM your_table_name yt
   WHERE yt.your_date_column >= dr.start_date 
     AND yt.your_date_column <= dr.end_date
   ```
3. Add your specific SELECT columns and any additional WHERE conditions
4. Save as a Redash query

## Key SQL Functions Used

- `DATE_TRUNC('month', CURRENT_DATE)` - Gets first day of current month
- `EXTRACT(DOW FROM CURRENT_DATE)` - Gets day of week (0=Sunday, 1=Monday, etc.)
- `INTERVAL` calculations - Subtracts days to find the most recent Sunday

## Database Compatibility

This query uses standard SQL functions that work with:
- PostgreSQL
- Most SQL databases supported by Redash

For other databases, you may need to adjust the date functions accordingly.