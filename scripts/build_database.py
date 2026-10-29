#!/usr/bin/env python3
"""Import the Olist CSV files into data/processed/olist.duckdb."""
from __future__ import annotations
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
OUTPUT = ROOT / 'data' / 'processed'

TABLE_FILES = {
    'olist_ecommerce': {
        'customers': 'olist_customers_dataset.csv',
        'geolocation': 'olist_geolocation_dataset.csv',
        'order_items': 'olist_order_items_dataset.csv',
        'order_payments': 'olist_order_payments_dataset.csv',
        'order_reviews': 'olist_order_reviews_dataset.csv',
        'orders': 'olist_orders_dataset.csv',
        'products': 'olist_products_dataset.csv',
        'sellers': 'olist_sellers_dataset.csv',
        'category_translation': 'product_category_name_translation.csv',
    },
    'olist_marketing': {
        'marketing_qualified_leads': 'olist_marketing_qualified_leads_dataset.csv',
        'closed_deals': 'olist_closed_deals_dataset.csv',
    },
}


def qident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def main():
    try:
        import duckdb
    except ImportError:
        raise SystemExit('Install requirements first: pip install -r requirements.txt')
    OUTPUT.mkdir(exist_ok=True, parents=True)
    dbpath = OUTPUT / 'olist.duckdb'
    con = duckdb.connect(str(dbpath))
    status = []
    for folder, mapping in TABLE_FILES.items():
        con.execute(f'CREATE SCHEMA IF NOT EXISTS {qident(folder)}')
        for table, filename in mapping.items():
            file = RAW / folder / filename
            qualified = f'{qident(folder)}.{qident(table)}'
            if not file.exists():
                print(f'MISSING: {folder}/{filename}')
                status.append([folder, table, filename, 0, 'MISSING'])
                continue
            print(f'IMPORT: {folder}.{table} <- {file.name}')
            try:
                # Type-safe ingestion: preserves all source values as text; analyst views cast selectively.
                con.execute(f"CREATE OR REPLACE TABLE {qualified} AS SELECT * FROM read_csv_auto(?, all_varchar=true, sample_size=-1)", [str(file)])
                count = con.execute(f'SELECT COUNT(*) FROM {qualified}').fetchone()[0]
                status.append([folder, table, filename, count, 'LOADED'])
                print(f'  {count:,} rows')
            except Exception as e:
                status.append([folder, table, filename, 0, f'ERROR: {e}'])
                print(f'  ERROR: {e}')
    con.execute('CREATE SCHEMA IF NOT EXISTS marts')

    def loaded(schema, table):
        return any(row[0] == schema and row[1] == table and row[4] == 'LOADED' for row in status)

    if all(loaded('olist_marketing', x) for x in ['marketing_qualified_leads', 'closed_deals']) and loaded('olist_ecommerce', 'order_items'):
        con.execute('''
        CREATE OR REPLACE VIEW marts.olist_seller_growth AS
        WITH seller_sales AS (
            SELECT seller_id,
                COUNT(DISTINCT order_id) AS num_orders,
                COUNT(*) AS num_items,
                SUM(TRY_CAST(price AS DOUBLE)) AS item_sales_value,
                SUM(TRY_CAST(freight_value AS DOUBLE)) AS freight_value
            FROM olist_ecommerce.order_items GROUP BY 1
        )
        , unique_deals AS (
            SELECT * EXCLUDE (rn) FROM (
                SELECT d.*, ROW_NUMBER() OVER (
                  PARTITION BY d.seller_id ORDER BY d.won_date DESC NULLS LAST, d.mql_id
                ) AS rn
                FROM olist_marketing.closed_deals d
                WHERE d.seller_id IS NOT NULL AND d.seller_id <> ''
            ) WHERE rn = 1
        )
        SELECT d.mql_id, d.seller_id, d.won_date, d.business_segment,
            m.first_contact_date, m.origin AS marketing_origin,
            s.num_orders, s.num_items, s.item_sales_value, s.freight_value
        FROM unique_deals d
        LEFT JOIN olist_marketing.marketing_qualified_leads m ON m.mql_id = d.mql_id
        LEFT JOIN seller_sales s ON s.seller_id = d.seller_id
        ''')
        print('CREATED: marts.olist_seller_growth (real seller_id join)')
    else:
        print('SKIPPED: marts.olist_seller_growth (needs both Olist datasets)')

    csv_path = OUTPUT / 'import_status.csv'
    with csv_path.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['domain', 'table', 'source_file', 'row_count', 'status'])
        writer.writerows(status)
    print('\nDATABASE:', dbpath)
    print('IMPORT REPORT:', csv_path)
    print('Complete:', sum(r[-1] == 'LOADED' for r in status), '/', len(status), 'tables')
    con.close()


if __name__ == '__main__':
    main()
