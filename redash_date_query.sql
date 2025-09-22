-- Redash Query: First of Month to Most Recent Sunday
-- This query creates a date range from the first day of the current month 
-- to the most recent Sunday (for weekly completeness checks that run on Monday)

WITH date_calculations AS (
  SELECT 
    -- Get the first day of the current month
    DATE_TRUNC('month', CURRENT_DATE) AS first_of_month,
    
    -- Get the most recent Sunday
    -- If today is Sunday, use yesterday's Sunday
    -- Otherwise, find the most recent Sunday
    CASE 
      WHEN EXTRACT(DOW FROM CURRENT_DATE) = 0 THEN -- Today is Sunday
        CURRENT_DATE - INTERVAL '7 days'
      ELSE 
        CURRENT_DATE - INTERVAL '1 day' * EXTRACT(DOW FROM CURRENT_DATE)
    END AS most_recent_sunday
),
final_dates AS (
  SELECT 
    first_of_month,
    most_recent_sunday,
    -- Ensure we don't go beyond the current month
    LEAST(most_recent_sunday, DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day') AS end_date
  FROM date_calculations
)

-- Your main query goes here - replace this with your actual data query
SELECT 
  fd.first_of_month AS start_date,
  fd.end_date,
  -- Example: selecting data within the date range
  -- Replace 'your_table' and 'date_column' with your actual table and date column
  /*
  your_data_column1,
  your_data_column2
  FROM your_table yt
  CROSS JOIN final_dates fd
  WHERE yt.date_column >= fd.first_of_month 
    AND yt.date_column <= fd.end_date
  */
  
  -- For demonstration, showing the calculated date range
  'Data from ' || fd.first_of_month::text || ' to ' || fd.end_date::text AS date_range_info
FROM final_dates fd;

-- Alternative simpler version (if your database supports these functions):
/*
SELECT 
  DATE_TRUNC('month', CURRENT_DATE) AS start_date,
  CURRENT_DATE - INTERVAL '1 day' * (EXTRACT(DOW FROM CURRENT_DATE) + CASE WHEN EXTRACT(DOW FROM CURRENT_DATE) = 0 THEN 7 ELSE 0 END) AS end_date
*/