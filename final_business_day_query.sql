WITH date_parameters AS (
    SELECT
        -- Calculate first business day of current month
        CASE 
            WHEN DAYOFWEEK(DATE_FORMAT(CURDATE(), '%Y-%m-01')) = 1 THEN -- First is Sunday
                DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 1 DAY)
            WHEN DAYOFWEEK(DATE_FORMAT(CURDATE(), '%Y-%m-01')) = 7 THEN -- First is Saturday
                DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 2 DAY)
            ELSE 
                DATE_FORMAT(CURDATE(), '%Y-%m-01') -- First is a weekday
        END AS first_biz_day,
        
        -- Calculate second business day of current month
        CASE 
            WHEN DAYOFWEEK(DATE_FORMAT(CURDATE(), '%Y-%m-01')) = 1 THEN -- First is Sunday
                DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 2 DAY)
            WHEN DAYOFWEEK(DATE_FORMAT(CURDATE(), '%Y-%m-01')) = 7 THEN -- First is Saturday
                DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 3 DAY)
            WHEN DAYOFWEEK(DATE_FORMAT(CURDATE(), '%Y-%m-01')) = 6 THEN -- First is Friday
                DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 4 DAY)
            ELSE -- First is Mon-Thu
                DATE_ADD(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 1 DAY)
        END AS second_biz_day
),
final_dates AS (
    SELECT 
        first_biz_day,
        second_biz_day,
        
        -- Start date logic
        CASE 
            WHEN CURDATE() IN (first_biz_day, second_biz_day) THEN 
                DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), '%Y-%m-01') -- Previous month start
            ELSE 
                DATE_FORMAT(CURDATE(), '%Y-%m-01') -- Current month start
        END AS report_start_date,
        
        -- End date logic
        CASE 
            WHEN CURDATE() IN (first_biz_day, second_biz_day) THEN 
                LAST_DAY(DATE_SUB(CURDATE(), INTERVAL 1 MONTH)) -- Previous month end
            ELSE 
                DATE_SUB(CURDATE(), INTERVAL 1 DAY) -- Yesterday
        END AS report_end_date
        
    FROM date_parameters
)

SELECT 
    report_start_date,
    report_end_date
FROM final_dates