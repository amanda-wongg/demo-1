SELECT 
    CONCAT('https://app.gusto.com/panda/bank_transactions/',bt.id) as bank_transaction_id,
    bt.date as bank_transaction_date,
    bt.payment_method as payment_method,
    bt.bank_account as bank_account,
    bt.credit_amount as credit_amount,
    bt.debit_amount as debit_amount,
    
    -- ADD DESCRIPTION FROM OTHER TABLE
    desc_table.description as transaction_description,
    desc_table.memo as transaction_memo,
    desc_table.reference_number as reference_number,
    
    aac.body,
    r.created_at as reconciled_at,
    r.record_id as transmission_id,
    r.record_type as record_type,
    case when r.auditor_id is null then 'unclaimed'
     else u.slack_name
     end as reconciler
FROM bi.bank_transactions bt
LEFT JOIN zenpayroll_production.reconciliations r
ON bt.id = r.transaction_id
LEFT JOIN zenpayroll_production.active_admin_comments aac
ON (bt.id = aac.resource_id AND aac.resource_type = 'BankTransaction')
left join zenpayroll_production_no_pii.users as u on r.auditor_id = u.id

-- ADD THIS JOIN (replace with actual table/field names)
LEFT JOIN [DATABASE_NAME].[TABLE_WITH_DESCRIPTIONS] desc_table
ON bt.[LINKING_FIELD] = desc_table.[LINKING_FIELD]

WHERE r.auditor_id IS NOT NULL
AND r.created_at >= '{{ Date Range.start }}'
and r.created_at <= '{{ Date Range.end }}'
AND bt.reconciled = 'true'
AND (bt.credit_amount > 10000 OR bt.debit_amount > 10000)
ORDER BY reconciled_at DESC