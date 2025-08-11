-- SQLite
-- Example: updating expiry_date based on SKU from CSV data
UPDATE product_product
SET expiry_date = CASE sku
    WHEN '100001' THEN '2025-09-15'
    WHEN '100002' THEN '2025-12-01'
    WHEN '100003' THEN '2025-08-30'
    WHEN '100004' THEN '2025-11-10'
    WHEN '100005' THEN '2025-10-05'
    WHEN '100006' THEN '2026-01-20'
    WHEN '100007' THEN '2025-09-01'
    WHEN '100008' THEN '2025-08-25'
    WHEN '100009' THEN '2025-12-15'
    WHEN '100010' THEN '2025-09-20'
    -- Add more SKUs from your CSV here
END
WHERE sku IN (
    '100001','100002','100003','100004','100005',
    '100006','100007','100008','100009','100010'
);
