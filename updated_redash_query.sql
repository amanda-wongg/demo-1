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

-- Determine the first day of the starting month for month series generation
first_month_of_report AS (
    SELECT DATE_FORMAT(dp.report_start_date, '%Y-%m-01') AS first_day_of_start_month
    FROM date_parameters dp
),

-- Helper CTE to generate digits 0-9
digits_0_9 AS (
    SELECT 0 AS d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL
    SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9
),

-- Helper CTE to generate digits 0-11 (used for tens multiplier to get 0-119 for month offsets)
digits_0_11 AS ( 
    SELECT 0 AS d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL
    SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL
    SELECT 10 UNION ALL SELECT 11
),

-- Generate a sequence of numbers (0 to 119) to be used as month offsets (covers 10 years)
numbers_sequence AS (
    SELECT (d1.d + (d2.d * 10)) AS month_offset
    FROM digits_0_9 d1        -- For the units digit (0-9)
    CROSS JOIN digits_0_11 d2 -- For the tens place (d2.d * 10 results in 0, 10, ..., 110)
),

-- Generate a series of the first day of each month within the report date range
month_series_for_report_points AS (
    SELECT
        CAST(DATE_ADD(CAST(fmr.first_day_of_start_month AS DATE), INTERVAL ns.month_offset MONTH) AS DATE) AS current_month_start
    FROM numbers_sequence ns
    CROSS JOIN first_month_of_report fmr
    CROSS JOIN date_parameters dp
    WHERE
        DATE_ADD(CAST(fmr.first_day_of_start_month AS DATE), INTERVAL ns.month_offset MONTH) <= dp.report_end_date
        AND CAST(fmr.first_day_of_start_month AS DATE) <= dp.report_end_date -- Ensure report range itself is valid
        AND ns.month_offset < 240 -- Consistent with numbers_sequence generation limit (20 years)
),
-- select * from month_series_for_report_points where current_month_start >= '2025-01-01'

-- Base CTE for origination accounts
origination_accounts_base AS (
    SELECT
        oa.id AS origination_account_id,
        CONCAT_WS('-', ob.name, oa.purpose, oa.id) AS origination_account_full
    FROM origination_accounts AS oa
    LEFT JOIN origination_banks AS ob ON oa.origination_bank_id = ob.id
    GROUP BY 1, 2
),

-- Filter for the specific origination account(s)
relevant_origination_accounts AS (
    SELECT
        oa.origination_account_id,
        oa.origination_account_full
    FROM origination_accounts_base AS oa
    WHERE (oa.origination_account_full in ({{Origination Account}}))
    -- add parameter back once Platform Accounting confirms this list: https://redash.zp-int.com/queries/121815/source
    -- https://gustohq.slack.com/archives/C04PT6SPH8Q/p1747870347457469?thread_ts=1747769234.942189&cid=C04PT6SPH8Q
    -- WHERE oa.origination_account_id in (26, 28, 31) -- Hardcoded for origination_account_id = 26
    GROUP BY 1, 2
),

-- report_points_cte defines the "period_label_month_start" and the actual "as_of_date" 
-- for calculations for each month in the range.
report_points_cte AS (
    SELECT
        ms.current_month_start AS period_label_month_start,
        CASE
            -- If the current month in the series is the same month/year as the overall report_end_date
            WHEN YEAR(ms.current_month_start) = YEAR(dp.report_end_date) AND MONTH(ms.current_month_start) = MONTH(dp.report_end_date)
            THEN dp.report_end_date -- The 'as of' date is the overall report_end_date
            ELSE LAST_DAY(ms.current_month_start) -- Otherwise, it's the last day of the current month from the series
        END AS as_of_date,
        roa.origination_account_id,
        roa.origination_account_full
    FROM month_series_for_report_points ms
    CROSS JOIN date_parameters dp
    CROSS JOIN relevant_origination_accounts roa
    WHERE ms.current_month_start IS NOT NULL -- Ensure month series actually produced rows
),

-- Collect all BAI2 bank transactions for the specified account
all_bai2_transactions_for_account AS (
    SELECT
        bai.origination_account_id,
        bai.date AS bai2_bt_dt,
        CASE
            WHEN bai.transaction_type = 2 THEN (bai.amount * -1) / 100.00 -- Assumes bai.amount is integer cents; result is precise DECIMAL
            WHEN bai.transaction_type = 4 THEN bai.amount / 100.00       -- Assumes bai.amount is integer cents; result is precise DECIMAL
            ELSE NULL
        END AS bai2_signed_amount, -- This is the precise dollar value for summing
        bai.created_at AS created_at_utc
    FROM bank_transactions AS bai
    JOIN relevant_origination_accounts AS roa ON bai.origination_account_id = roa.origination_account_id
    JOIN date_parameters dp ON bai.date <= dp.report_end_date -- <<< PRE-FILTER ADDED
    WHERE bai.transaction_type IN (2, 4)
),

-- Collect all closing bank balance transactions for the specified account
all_closing_ledgers_for_account AS (
    SELECT
        c.origination_account_id,
        c.date AS cbb_date,
        ROUND((c.amount / 100.00), 2) AS closing_ledger_amount, -- Assumes c.amount is integer cents; converted to DECIMAL dollars and rounded
        c.created_at AS created_at_utc
    FROM bank_transactions AS c
    JOIN relevant_origination_accounts AS roa ON c.origination_account_id = roa.origination_account_id
    JOIN date_parameters dp ON c.date <= dp.report_end_date -- <<< PRE-FILTER ADDED
    WHERE c.transaction_type = 0
      AND c.type_description = 'Closing Ledger'
),

-- Calculate running sum of precise BAI2 dollar transactions UP TO each 'as_of_date'
running_bai2_sums AS (
    SELECT
        rp.period_label_month_start,
        rp.as_of_date,
        rp.origination_account_id,
        SUM(bt.bai2_signed_amount) AS total_bai2_signed_sum_running, -- Sum of precise DECIMAL dollar values
        MAX(bt.created_at_utc) AS max_bai2_bt_created_utc_running
    FROM report_points_cte rp
    LEFT JOIN all_bai2_transactions_for_account bt
        ON rp.origination_account_id = bt.origination_account_id
        AND bt.bai2_bt_dt <= rp.as_of_date
    GROUP BY rp.period_label_month_start, rp.as_of_date, rp.origination_account_id -- Group by all unique fields of a report point
),

-- Determine the latest closing bank balance ON OR BEFORE each 'as_of_date'
latest_closing_ledgers AS (
    SELECT
        rp.period_label_month_start,
        rp.as_of_date,
        rp.origination_account_id,
        cl.closing_ledger_amount, -- This is already rounded to 2 decimal places
        cl.cbb_date AS closing_ledger_actual_date,
        cl.created_at_utc AS closing_ledger_created_utc,
        ROW_NUMBER() OVER (
            PARTITION BY rp.period_label_month_start, rp.as_of_date, rp.origination_account_id -- Partition by all unique fields of a report point
            ORDER BY cl.cbb_date DESC, cl.created_at_utc DESC
        ) as rn
    FROM report_points_cte rp
    LEFT JOIN all_closing_ledgers_for_account cl
        ON rp.origination_account_id = cl.origination_account_id
        AND cl.cbb_date <= rp.as_of_date
)

-- Final selection combining data for each report point
SELECT
    rp.period_label_month_start AS month_start,
    rp.as_of_date AS end_date, -- This is the 'as_of_date' used for calculations
    -- rp.origination_account_id,
    rp.origination_account_full, -- for readability, e.g. Grasshopper-operations-31
    ROUND(rbs.total_bai2_signed_sum_running, 2) AS bai2_sum, -- Sum is rounded here
    lcl.closing_ledger_amount AS closing_bank_balance, -- Already rounded in its CTE
    (ROUND(COALESCE(rbs.total_bai2_signed_sum_running, 0.00), 2) - COALESCE(lcl.closing_ledger_amount, 0.00)) AS signed_variance,
    ABS((ROUND(COALESCE(rbs.total_bai2_signed_sum_running, 0.00), 2) - COALESCE(lcl.closing_ledger_amount, 0.00))) AS absolute_variance,
    CONVERT_TZ(rbs.max_bai2_bt_created_utc_running, 'UTC', 'America/Los_Angeles') AS max_bai2_bt_created_pt,
    CONVERT_TZ(lcl.closing_ledger_created_utc, 'UTC', 'America/Los_Angeles') AS closing_bank_balance_created_pt
FROM report_points_cte rp
LEFT JOIN running_bai2_sums rbs
    ON rp.period_label_month_start = rbs.period_label_month_start AND rp.as_of_date = rbs.as_of_date AND rp.origination_account_id = rbs.origination_account_id
LEFT JOIN latest_closing_ledgers lcl
    ON rp.period_label_month_start = lcl.period_label_month_start AND rp.as_of_date = lcl.as_of_date AND rp.origination_account_id = lcl.origination_account_id AND lcl.rn = 1
WHERE 1=1
AND (rbs.total_bai2_signed_sum_running IS NOT NULL OR lcl.closing_ledger_amount IS NOT NULL) -- Only include rows if there's BAI2 sum data and/or bank balance data
ORDER BY rp.origination_account_id ASC, rp.period_label_month_start DESC