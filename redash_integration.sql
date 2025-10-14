-- Redash Query Template for Variance Alerts with Historical Exclusions
-- This query filters out known historical variances before applying the alert threshold

WITH historical_exclusions AS (
  -- Define your known historical variances here
  -- You can populate this from your variance_alert_system.py database
  SELECT 
    '2024-01-15'::date as exclusion_date,
    500.00 as exclusion_amount,
    'reconciliation' as exclusion_category,
    'Monthly reconciliation adjustment' as exclusion_description
  
  UNION ALL
  
  SELECT 
    '2024-02-01'::date,
    1200.00,
    'accruals',
    'Year-end accrual adjustment'
    
  UNION ALL
  
  SELECT 
    '2024-03-15'::date,
    750.00,
    'reconciliation', 
    'Quarterly adjustment'
    
  -- Add more historical exclusions as needed
),

variance_patterns AS (
  -- Define patterns for automatic exclusion
  SELECT 
    'reconciliation' as pattern_category,
    100.00 as threshold_amount,
    'reconciliation' as description_pattern
    
  UNION ALL
  
  SELECT
    'accruals',
    50.00,
    'accrual'
),

current_variances AS (
  -- Your main variance query goes here
  -- Replace this with your actual variance calculation
  SELECT 
    report_date,
    category,
    variance_amount,
    description,
    -- Add any other relevant fields
    department,
    account_code
  FROM your_variance_table
  WHERE report_date >= CURRENT_DATE - INTERVAL '30 days'
    AND ABS(variance_amount) > 0  -- Only non-zero variances
),

filtered_variances AS (
  SELECT 
    cv.*,
    CASE 
      WHEN he.exclusion_date IS NOT NULL 
        AND ABS(cv.variance_amount - he.exclusion_amount) <= 0.01
        AND cv.category = he.exclusion_category
      THEN 'historical_exclusion'
      
      WHEN vp.pattern_category IS NOT NULL 
        AND cv.category = vp.pattern_category
        AND ABS(cv.variance_amount) <= vp.threshold_amount
      THEN 'pattern_exclusion'
      
      WHEN vp.description_pattern IS NOT NULL
        AND cv.description ILIKE '%' || vp.description_pattern || '%'
        AND ABS(cv.variance_amount) <= vp.threshold_amount  
      THEN 'pattern_exclusion'
      
      ELSE 'alert_required'
    END as exclusion_status
    
  FROM current_variances cv
  LEFT JOIN historical_exclusions he ON (
    cv.report_date = he.exclusion_date
    AND cv.category = he.exclusion_category
    AND ABS(cv.variance_amount - he.exclusion_amount) <= 0.01
  )
  LEFT JOIN variance_patterns vp ON (
    cv.category = vp.pattern_category
    OR cv.description ILIKE '%' || vp.description_pattern || '%'
  )
)

-- Final query: Only return variances that should trigger alerts
SELECT 
  report_date,
  category,
  variance_amount,
  description,
  department,
  account_code,
  exclusion_status,
  -- Add alert severity based on amount
  CASE 
    WHEN ABS(variance_amount) >= 10000 THEN 'CRITICAL'
    WHEN ABS(variance_amount) >= 5000 THEN 'HIGH' 
    WHEN ABS(variance_amount) >= 1000 THEN 'MEDIUM'
    ELSE 'LOW'
  END as alert_severity
  
FROM filtered_variances
WHERE exclusion_status = 'alert_required'
  AND ABS(variance_amount) > {{threshold|0}}  -- Redash parameter for threshold
ORDER BY ABS(variance_amount) DESC, report_date DESC;

-- For Redash Alert Configuration:
-- 1. Set the alert condition to: "Query returns results" 
-- 2. Set threshold parameter to 0 (since we're handling filtering in the query)
-- 3. The query will only return rows that should trigger alerts