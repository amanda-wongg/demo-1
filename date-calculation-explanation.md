# Date Calculation Explanation

## How the Previous Week Calculation Works

The key is this CTE (Common Table Expression) at the top:

```sql
with date_params as (
  select
    -- Previous Monday (start of previous week)
    dateadd(day, -(datepart(weekday, getdate()) + 5) % 7, getdate()) as prev_monday,
    -- Previous Friday (end of previous week)  
    dateadd(day, -(datepart(weekday, getdate()) + 1) % 7, getdate()) as prev_friday
)
```

## Date Logic Breakdown

### Previous Monday Calculation:
`dateadd(day, -(datepart(weekday, getdate()) + 5) % 7, getdate())`

**How it works:**
- `datepart(weekday, getdate())` returns: Sunday=1, Monday=2, Tuesday=3, etc.
- We add 5 to shift the calculation
- Use modulo 7 to get days to subtract
- `dateadd(day, -X, getdate())` goes back X days from today

**Examples (if today is):**
- **Monday (12/16)**: `(2 + 5) % 7 = 0` → Go back 0 days = Previous Monday (12/9)
- **Tuesday (12/17)**: `(3 + 5) % 7 = 1` → Go back 1 day = Previous Monday (12/9) 
- **Wednesday (12/18)**: `(4 + 5) % 7 = 2` → Go back 2 days = Previous Monday (12/9)
- **Sunday (12/22)**: `(1 + 5) % 7 = 6` → Go back 6 days = Previous Monday (12/9)

### Previous Friday Calculation:
`dateadd(day, -(datepart(weekday, getdate()) + 1) % 7, getdate())`

**Examples (if today is):**
- **Monday (12/16)**: `(2 + 1) % 7 = 3` → Go back 3 days = Previous Friday (12/13)
- **Tuesday (12/17)**: `(3 + 1) % 7 = 4` → Go back 4 days = Previous Friday (12/13)
- **Sunday (12/22)**: `(1 + 1) % 7 = 2` → Go back 2 days = Previous Friday (12/20)

## What Changed in Your Query

### Before (Manual Parameters):
```sql
and pr.bank_transaction_date between '{{PR Date Range.start}}'
and '{{PR Date Range.end}}'
```

### After (Automatic Dates):
```sql
cross join date_params dp  -- Join with calculated dates
-- ...
and pr.bank_transaction_date between dp.prev_monday and dp.prev_friday
```

## Testing the Date Logic

You can test the date calculation separately:

```sql
-- Test query to see what dates will be used
with date_params as (
  select
    dateadd(day, -(datepart(weekday, getdate()) + 5) % 7, getdate()) as prev_monday,
    dateadd(day, -(datepart(weekday, getdate()) + 1) % 7, getdate()) as prev_friday,
    getdate() as today,
    datename(weekday, getdate()) as today_name
)
select 
  today,
  today_name,
  prev_monday,
  datename(weekday, prev_monday) as monday_check,
  prev_friday,
  datename(weekday, prev_friday) as friday_check,
  'Week of ' + convert(varchar, prev_monday, 101) + ' to ' + convert(varchar, prev_friday, 101) as date_range
from date_params;
```

## Schedule Recommendations

### For Monday Morning Alerts:
- **Schedule**: Every Monday at 9:00 AM
- **What it does**: Analyzes previous week (Monday-Friday)
- **Example**: On Monday 12/16, analyzes week of 12/9-12/13

### Alternative Schedules:
- **Tuesday Morning**: In case Monday is a holiday
- **Daily**: But only triggers if there are variances from previous week
- **Manual**: Run anytime to get previous week's data

## Benefits of This Approach

✅ **No manual date entry** - completely automated
✅ **Always gets previous business week** - Monday through Friday
✅ **Perfect for Monday morning reviews** - fresh data from last week
✅ **Consistent date ranges** - no human error in date selection
✅ **Works with webhook alerts** - no parameters needed

## Troubleshooting

### If dates look wrong:
1. Run the test query above to see what dates are calculated
2. Check your SQL Server's `@@DATEFIRST` setting (should be 7 for Sunday = 1)
3. Verify the timezone of your Redash server

### If you need different weeks:
- **Current week**: Change the calculation to get Monday-Friday of current week
- **Two weeks ago**: Add `-7` to both calculations
- **Month-end**: Use different date logic for end-of-month reconciliation