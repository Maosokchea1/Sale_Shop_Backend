-- Update pending orders
UPDATE orders SET total_amount_usd = 29.99 WHERE total_amount_usd IS NULL AND status = 'pending';
UPDATE orders SET total_amount_khr = 122959 WHERE total_amount_khr IS NULL AND status = 'pending';

-- Update paid orders
UPDATE orders SET total_amount_usd = 49.99, total_amount_khr = 204959 WHERE status = 'paid' AND total_amount_usd IS NULL;

-- Check results
SELECT id, order_number, status, total_amount_usd FROM orders;