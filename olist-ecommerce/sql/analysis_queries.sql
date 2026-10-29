-- Query the generated data/processed/olist.duckdb with DuckDB.
-- Marketing --> Closed Deals --> Seller --> Orders linkage (real seller_id join).
-- "item_sales_value" sums item prices, not payment totals and not net profit.
SELECT marketing_origin,
       COUNT(DISTINCT seller_id) AS won_sellers,
       SUM(COALESCE(num_orders,0)) AS seller_orders,
       SUM(COALESCE(item_sales_value,0)) AS item_sales_value
FROM marts.olist_seller_growth
GROUP BY 1
ORDER BY item_sales_value DESC;
