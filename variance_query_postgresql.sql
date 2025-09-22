with date_params as (
  select 
    current_date - ((date_part(dow, current_date) + 6) % 7)::int as start_date,
    current_date - ((date_part(dow, current_date) + 2) % 7)::int as end_date
),
cal as 
(
  select
    distinct date,
    business_day
  from
    bi.static_calendar
  where
    date between (
      select
        min(date)
      from
        bi.bank_transactions
    )
    and current_date - 1
),
banks as 
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
bank_name_populated_cal as 
(
  select
    cal.date,
    cal.business_day,
    banks.bank_account
  from
    cal
    left join banks on cal.date >= banks.md
    and cal.date <= current_date
  order by
    cal.date desc
),
available_bt_totals as 
(
  select
    bi.date,
    bi.bank_account || '-' || bi.origination_account_id as bank_account,
    sum(bi.signed_amount) daily_bt_amount
  from
    bi.bank_transactions as bi
  group by
    1,
    2
),
daily_bt_totals as 
(
  select
    bnpc.date,
    bnpc.business_day,
    bnpc.bank_account,
    coalesce(abt.daily_bt_amount, 0) daily_bt_amount
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
    ) daily_balance
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
    and pr.bank_transaction_date between dp.start_date and dp.end_date
  group by
    1
),
what_is_unreconciled as (
  SELECT
    bt.bank_account || '-' || bt.origination_account_id as bank_account,
    SUM(coalesce(bt.credit_amount, 0)) credit_total,
    SUM(coalesce(bt.debit_amount, 0)) debit_total,
    (coalesce(debit_total, 0) - coalesce(credit_total, 0)) as absolute_total
  FROM
    bi.bank_transactions bt
    cross join date_params dp
  WHERE
    bt.reconciled_at IS NULL
    AND bt.date >= dp.start_date
    AND bt.date <= dp.end_date
    AND bt.bank_account not like '%corporate%'
    AND bt.bank_account not like '%insurance%'
    AND bt.bank_account != 'Chase flex_pay_revenue'
  GROUP BY
    1
)
select
  dp.start_date as calculated_start_date,
  dp.end_date as calculated_end_date,
  prm.bank_account,
  prm.reconciled_payment_records,
  coalesce(bb1.date, dp.start_date) bt_date_1,
  coalesce(bb1.daily_balance, 0.00) bt_balance_1,
  bb2.date bt_date_2,
  bb2.daily_balance bt_balance_2,
  bt_balance_2 - bt_balance_1 as movement,
  movement - reconciled_payment_records as difference,
  coalesce(wiu.credit_total,0) as unreconciled_bt_credit,
  coalesce(wiu.debit_total, 0) as unreconciled_bt_debit,
  coalesce(wiu.absolute_total, 0) unreconciled_bt_absolute_total, 
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
      date = (select start_date - 1 from date_params)
  ) bb1 on prm.bank_account = bb1.bank_account
  left join (
    select
      *
    from
      rolled_up_daily_bt_totals
    where
      date = (select end_date from date_params)
  ) bb2 on prm.bank_account = bb2.bank_account
  left join what_is_unreconciled wiu on prm.bank_account = wiu.bank_account
order by 3 asc