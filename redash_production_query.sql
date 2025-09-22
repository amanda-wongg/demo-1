-- PRODUCTION REDASH QUERY
-- Date Range: First of Current Month to Most Recent Sunday
-- Use this query in Redash for your weekly completeness checks

WITH date_range AS (
  SELECT 
    -- Start date: First day of current month
    DATE_TRUNC('month', CURRENT_DATE) AS start_date,
    
    -- End date: Most recent Sunday
    -- If today is Sunday (DOW = 0), use the previous Sunday
    -- Otherwise, calculate days back to most recent Sunday
    CASE 
      WHEN EXTRACT(DOW FROM CURRENT_DATE) = 0 THEN 
        CURRENT_DATE - INTERVAL '7 days'
      ELSE 
        CURRENT_DATE - INTERVAL '1 day' * EXTRACT(DOW FROM CURRENT_DATE)
    END AS end_date
)

-- Replace this section with your actual data query
SELECT 
  dr.start_date,
  dr.end_date,
  
  -- Example data selection - replace with your actual columns and table
  -- Uncomment and modify the following lines for your actual query:
  /*
  COUNT(*) as record_count,
  your_column1,
  your_column2
  FROM your_table_name yt
  CROSS JOIN date_range dr
  WHERE yt.your_date_column >= dr.start_date 
    AND yt.your_date_column <= dr.end_date
  GROUP BY dr.start_date, dr.end_date, your_column1, your_column2
  ORDER BY your_column1
  */
  
  -- For testing purposes, showing the calculated date range
  CONCAT('Query will pull data from ', start_date::text, ' through ', end_date::text) as date_info

FROM date_range dr;