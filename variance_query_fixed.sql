-- Automatic Variance Query - Previous Monday to Friday Week
-- Redshift/PostgreSQL version - FIXED

with date_params as (
  -- Automatically calculate previous Monday to Friday week
  select 
    -- Find the Monday of the previous complete week
    dateadd(day, -(date_part(dow, getdate()) + 6) % 7, getdate())::date as start_date,
    -- Find the Friday of the previous complete week  
    dateadd(day, -(date_part(dow, getdate()) + 2) % 7, getdate())::date as end_date
),
cal as -- calendar for start of bt table and most up to date data
(
  select
    distinct date,
    business_day
  from
    bi.static_calendar -- add business day
  where
    date between (
      select
        min(date)
      from
        bi.bank_transactions
    )
    and dateadd(day, -1, getdate())  -- FIXED: was date_add
),
banks as -- returns bank info and first date that they appear
(
  select
    bank_account || '-' || origination_account_id as bank_account,
    min(date) md
  from
    bi.bank_transactions bi
  where
    bi.bank_account not like '%corporate%'
    and bi.bank_account not like '%health_insurance%'
    and bi.bank_account not like '%flex_pay%'
  group by
    1
),
bank_name_populated_cal as -- joins in bank info for every day after an individual banks min date
(
  select
    cal.date,
    cal.business_day,
    banks.bank_account
  from
    cal
    left join banks on cal.date >= banks.md
    and cal.date <= getdate()
  order by
    cal.date desc
),
available_bt_totals as --determines the daily bt totals for each bank and date --
(
  select
    bi.date -- will not include non-business days
,
    bi.bank_account || '-' || bi.origination_account_id as bank_account,
    sum(bi.signed_amount) daily_bt_amount
  from
    bi.bank_transactions as bi
  group by
    1,
    2
),
daily_bt_totals as -- taking all dates + bank names and joining dates where bts exists + bank names and converting nulls to 0
(
  select
    bnpc.date,
    bnpc.business_day,
    bnpc.bank_account,
    coalesce(abt.daily_bt_amount, 0) daily_bt_amount  -- FIXED: use coalesce instead of nvl
  from
    bank_name_populated_cal bnpc
    left join available_bt_totals abt on bnpc.date = abt.date
    and bnpc.bank_account = abt.bank_account
),
rolled_up_daily_bt_totals as -- includes incorrect SVB Operations from 10-01-2017 to 12-20-2020
(
  select
    date,
    business_day,
    bank_account,
    sum(daily_bt_amount) over (
      partition by bank_account
      order by
        date asc rows between unbounded preceding
        and current row
    ) daily_balance -- rolling cash balance
  from
    daily_bt_totals
),
payment_record_movment as (
  select
    pr.bank_account || '-' || pr.origination_account_id as bank_account,
    sum(pr.signed_amount) reconciled_payment_records
  from
    bi.payment_records pr
    cross join date_params dp  -- Use our calculated dates
  where
    pr.reconciled is true
    and pr.bank_account not like '%flex%'
    and pr.bank_account not like '%corp%'
    and pr.bank_account not like '%health%'
    and pr.bank_transaction_date between dp.start_date and dp.end_date  -- Auto dates
  group by
    1
),
what_is_unreconciled as (
  SELECT
    bt.bank_account || '-' || bt.origination_account_id as bank_account,
    SUM(coalesce(bt.credit_amount, 0)) credit_total,  -- FIXED: use coalesce
    SUM(coalesce(bt.debit_amount, 0)) debit_total,    -- FIXED: use coalesce
    (coalesce(debit_total, 0) - coalesce(credit_total, 0)) as absolute_total
  FROM
    bi.bank_transactions bt
    cross join date_params dp  -- Use our calculated dates
  WHERE
    bt.reconciled_at IS NULL
    AND bt.date >= dp.start_date     -- Auto dates
    AND bt.date <= dp.end_date       -- Auto dates
    AND bt.bank_account not like '%corporate%'
    AND bt.bank_account not like '%insurance%'
    AND bt.bank_account != 'Chase flex_pay_revenue'
  GROUP BY
    1
)
select
  -- Show the date range being used (for verification)
  dp.start_date as calculated_start_date,
  dp.end_date as calculated_end_date,
  
  -- Your original columns
  prm.bank_account,
  prm.reconciled_payment_records,
  coalesce(bb1.date, dp.start_date) bt_date_1,      -- FIXED: use coalesce
  coalesce(bb1.daily_balance, 0.00) bt_balance_1,   -- FIXED: use coalesce
  bb2.date bt_date_2,
  bb2.daily_balance bt_balance_2,
  bt_balance_2 - bt_balance_1 as movement,
  movement - reconciled_payment_records as difference,
  coalesce(wiu.credit_total,0) as unreconciled_bt_credit,        -- FIXED: use coalesce
  coalesce(wiu.debit_total, 0) as unreconciled_bt_debit,         -- FIXED: use coalesce
  coalesce(wiu.absolute_total, 0) unreconciled_bt_absolute_total, -- FIXED: use coalesce
  movement - reconciled_payment_records - coalesce(wiu.absolute_total, 0) as variance
from
  date_params dp
  cross join payment_record_movment prm
  left join (
    select
      *
    from
      rolled_up_daily_bt_totals
    where
      date = (select dateadd(day, -1, start_date) from date_params)  -- Auto date
  ) bb1 on prm.bank_account = bb1.bank_account
  left join (
    select
      *
    from
      rolled_up_daily_bt_totals
    where
      date = (select end_date from date_params)  -- Auto date
  ) bb2 on prm.bank_account = bb2.bank_account
  left join what_is_unreconciled wiu on prm.bank_account = wiu.bank_account
order by 3 asc