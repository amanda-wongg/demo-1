-- Testing the date logic for Redash query
-- Example 1: Today is 9/22/25 (Monday) - should return 9/1/25 to 9/21/25
-- Example 2: Today is 9/29/25 (Monday) - should return 9/1/25 to 9/28/25

-- Test with 9/22/25 (Monday)
WITH test_date_1 AS (
  SELECT '2025-09-22'::DATE AS test_current_date
),
date_calc_1 AS (
  SELECT 
    test_current_date,
    DATE_TRUNC('month', test_current_date) AS first_of_month,
    test_current_date - INTERVAL '1 day' * EXTRACT(DOW FROM test_current_date) AS most_recent_sunday,
    EXTRACT(DOW FROM test_current_date) AS day_of_week -- 0=Sunday, 1=Monday, etc.
  FROM test_date_1
)
SELECT 
  'Test 1: 9/22/25 (Monday)' AS test_case,
  test_current_date,
  day_of_week,
  first_of_month AS start_date,
  most_recent_sunday AS end_date,
  'Expected: 2025-09-01 to 2025-09-21' AS expected_result
FROM date_calc_1

UNION ALL

-- Test with 9/29/25 (Monday) 
SELECT 
  'Test 2: 9/29/25 (Monday)' AS test_case,
  '2025-09-29'::DATE AS test_current_date,
  EXTRACT(DOW FROM '2025-09-29'::DATE) AS day_of_week,
  DATE_TRUNC('month', '2025-09-29'::DATE) AS start_date,
  '2025-09-29'::DATE - INTERVAL '1 day' * EXTRACT(DOW FROM '2025-09-29'::DATE) AS end_date,
  'Expected: 2025-09-01 to 2025-09-28' AS expected_result

UNION ALL

-- Test with a Sunday to verify logic
SELECT 
  'Test 3: 9/21/25 (Sunday)' AS test_case,
  '2025-09-21'::DATE AS test_current_date,
  EXTRACT(DOW FROM '2025-09-21'::DATE) AS day_of_week,
  DATE_TRUNC('month', '2025-09-21'::DATE) AS start_date,
  CASE 
    WHEN EXTRACT(DOW FROM '2025-09-21'::DATE) = 0 THEN 
      '2025-09-21'::DATE - INTERVAL '7 days'
    ELSE 
      '2025-09-21'::DATE - INTERVAL '1 day' * EXTRACT(DOW FROM '2025-09-21'::DATE)
  END AS end_date,
  'Expected: 2025-09-01 to 2025-09-14' AS expected_result;