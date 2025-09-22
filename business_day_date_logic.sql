WITH date_parameters AS (
    SELECT
        -- Helper: Get the first day of current month
        DATE_FORMAT(CURDATE(), '%Y-%m-01') AS first_of_current_month,
        
        -- Helper: Get the first business day of current month
        CASE 
            WHEN DAYOFWEEK(DATE_FORMAT(CURDATE(), '%Y-%m-01')) = 1 THEN -- First is Sunday
                DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 1 DAY)
            WHEN DAYOFWEEK(DATE_FORMAT(CURDATE(), '%Y-%m-01')) = 7 THEN -- First is Saturday
                DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 2 DAY)
            ELSE 
                DATE_FORMAT(CURDATE(), '%Y-%m-01') -- First is a weekday
        END AS first_business_day_current_month,
        
        -- Helper: Get the second business day of current month
        CASE 
            WHEN DAYOFWEEK(DATE_FORMAT(CURDATE(), '%Y-%m-01')) = 1 THEN -- First is Sunday, so 1st biz day is Mon, 2nd is Tue
                DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 2 DAY)
            WHEN DAYOFWEEK(DATE_FORMAT(CURDATE(), '%Y-%m-01')) = 7 THEN -- First is Saturday, so 1st biz day is Mon, 2nd is Tue
                DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 3 DAY)
            WHEN DAYOFWEEK(DATE_FORMAT(CURDATE(), '%Y-%m-01')) = 6 THEN -- First is Friday, so 2nd biz day is next Tuesday
                DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 4 DAY)
            ELSE -- First is Mon-Thu, so 2nd business day is next day
                DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 1 DAY)
        END AS second_business_day_current_month
),
date_logic AS (
    SELECT 
        first_of_current_month,
        first_business_day_current_month,
        second_business_day_current_month,
        
        -- Check if today is the 1st or 2nd business day of the month
        CASE 
            WHEN CURDATE() = first_business_day_current_month 
                 OR CURDATE() = second_business_day_current_month THEN 1
            ELSE 0
        END AS is_first_or_second_biz_day,
        
        -- Calculate start date
        CASE 
            WHEN CURDATE() = first_business_day_current_month 
                 OR CURDATE() = second_business_day_current_month THEN 
                DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), '%Y-%m-01') -- First day of previous month
            ELSE 
                first_of_current_month -- First day of current month
        END AS report_start_date,
        
        -- Calculate end date
        CASE 
            WHEN CURDATE() = first_business_day_current_month 
                 OR CURDATE() = second_business_day_current_month THEN 
                LAST_DAY(DATE_SUB(CURDATE(), INTERVAL 1 MONTH)) -- Last day of previous month
            ELSE 
                DATE_SUB(CURDATE(), INTERVAL 1 DAY) -- Yesterday
        END AS report_end_date
        
    FROM date_parameters
)

-- Final selection with the calculated dates
SELECT 
    report_start_date,
    report_end_date,
    is_first_or_second_biz_day,
    first_business_day_current_month,
    second_business_day_current_month,
    CONCAT('Query will pull data from ', report_start_date, ' through ', report_end_date) as date_info
FROM date_logic;