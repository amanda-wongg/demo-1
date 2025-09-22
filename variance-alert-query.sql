-- Bank Variance Alert Query - Previous Week Monday-Friday
-- Only returns accounts with non-zero variance for webhook alerts
-- Automatically calculates previous week's dates

-- Calculate previous week's Monday and Friday dynamically
with date_params as (
  select
    -- Previous Monday (start of previous week)
    dateadd(day, -(datepart(weekday, getdate()) + 5) % 7, getdate()) as prev_monday,
    -- Previous Friday (end of previous week)  
    dateadd(day, -(datepart(weekday, getdate()) + 1) % 7, getdate()) as prev_friday
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
    and date_add('day', -1, getdate())
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
    isnull(abt.daily_bt_amount, 0) daily_bt_amount
  from
    bank_name_populated_cal bnpc
    left join available_bt_totals abt on bnpc.date = abt.date
    and bnpc.bank_account = abt.bank_account
),
rolled_up_daily_bt_totals as 
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
    cross join date_params dp
  where
    pr.reconciled is true
    and pr.bank_account not like '%flex%'
    and pr.bank_account not like '%corp%'
    and pr.bank_account not like '%health%'
    and pr.bank_transaction_date between dp.prev_monday and dp.prev_friday
  group by
    1
),
what_is_unreconciled as (
  SELECT
    bank_account || '-' || origination_account_id as bank_account,
    SUM(isnull(credit_amount, 0)) credit_total,
    SUM(isnull(debit_amount, 0)) debit_total,
    (isnull(debit_total, 0) - isnull(credit_total, 0)) as absolute_total
  FROM
    bi.bank_transactions
    cross join date_params dp
  WHERE
    reconciled_at IS NULL
    AND date >= dp.prev_monday
    AND date <= dp.prev_friday
    AND bank_account not like '%corporate%'
    AND bank_account not like '%insurance%'
    AND bank_account != 'Chase flex_pay_revenue'
  GROUP BY
    1
)
select
  prm.bank_account,
  prm.reconciled_payment_records,
  dp.prev_monday as bt_date_1,
  coalesce(bb1.daily_balance, 0.00) bt_balance_1,
  dp.prev_friday as bt_date_2,
  bb2.daily_balance bt_balance_2,
  bt_balance_2 - bt_balance_1 as movement,
  movement - reconciled_payment_records as difference,
  isnull(wiu.credit_total,0) as unreconciled_bt_credit,
  isnull(wiu.debit_total, 0) as unreconciled_bt_debit,
  isnull(wiu.absolute_total, 0) unreconciled_bt_absolute_total, 
  movement - reconciled_payment_records - isnull(wiu.absolute_total, 0) as variance,
  -- Add formatted variance for Slack display
  case 
    when (movement - reconciled_payment_records - isnull(wiu.absolute_total, 0)) > 0 
    then '+$' + format(abs(movement - reconciled_payment_records - isnull(wiu.absolute_total, 0)), 'N2')
    when (movement - reconciled_payment_records - isnull(wiu.absolute_total, 0)) < 0 
    then '-$' + format(abs(movement - reconciled_payment_records - isnull(wiu.absolute_total, 0)), 'N2')
    else '$0.00'
  end as variance_formatted,
  -- Add severity level
  case 
    when abs(movement - reconciled_payment_records - isnull(wiu.absolute_total, 0)) > 10000 then '🚨 CRITICAL'
    when abs(movement - reconciled_payment_records - isnull(wiu.absolute_total, 0)) > 1000 then '⚠️ HIGH'
    when abs(movement - reconciled_payment_records - isnull(wiu.absolute_total, 0)) > 100 then '⚠️ MEDIUM'
    else '📋 LOW'
  end as severity,
  -- Show the week being analyzed
  'Week of ' + convert(varchar, dp.prev_monday, 101) + ' to ' + convert(varchar, dp.prev_friday, 101) as week_analyzed
from
  date_params dp
  cross join payment_record_movment prm
  left join (
    select *
    from rolled_up_daily_bt_totals
    where date = (select dateadd(day, -1, prev_monday) from date_params)
  ) bb1 on prm.bank_account = bb1.bank_account
  left join (
    select *
    from rolled_up_daily_bt_totals
    where date = (select prev_friday from date_params)
  ) bb2 on prm.bank_account = bb2.bank_account
  left join what_is_unreconciled wiu on prm.bank_account = wiu.bank_account
-- 🚨 KEY CHANGE: Only return accounts with variance != 0
where (movement - reconciled_payment_records - isnull(wiu.absolute_total, 0)) != 0
order by abs(movement - reconciled_payment_records - isnull(wiu.absolute_total, 0)) desc  -- Show biggest variances first