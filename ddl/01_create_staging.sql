-- DATA WAREHOUSE OLIST
-- Criação do esquema staging e das 9 tabelas brutas

CREATE SCHEMA IF NOT EXISTS staging;

DROP TABLE IF EXISTS staging.stg_orders CASCADE;
CREATE TABLE staging.stg_orders (
    order_id VARCHAR(50),
    customer_id VARCHAR(50),
    order_status VARCHAR(30),
    order_purchase_timestamp VARCHAR(40),
    order_approved_at VARCHAR(40),
    order_delivered_carrier_date VARCHAR(40),
    order_delivered_customer_date VARCHAR(40),
    order_estimated_delivery_date VARCHAR(40)
);

DROP TABLE IF EXISTS staging.stg_order_items CASCADE;
CREATE TABLE staging.stg_order_items (
    order_id VARCHAR(50),
    order_item_id INTEGER,
    product_id VARCHAR(50),
    seller_id VARCHAR(50),
    shipping_limit_date VARCHAR(40),
    price NUMERIC(12, 2),
    freight_value NUMERIC(12, 2)
);

DROP TABLE IF EXISTS staging.stg_order_payments CASCADE;
CREATE TABLE staging.stg_order_payments (
    order_id VARCHAR(50),
    payment_sequential INTEGER,
    payment_type VARCHAR(30),
    payment_installments INTEGER,
    payment_value NUMERIC(12, 2)
);

DROP TABLE IF EXISTS staging.stg_order_reviews CASCADE;
CREATE TABLE staging.stg_order_reviews (
    review_id VARCHAR(50),
    order_id VARCHAR(50),
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date VARCHAR(40),
    review_answer_timestamp VARCHAR(40)
);

DROP TABLE IF EXISTS staging.stg_customers CASCADE;
CREATE TABLE staging.stg_customers (
    customer_id VARCHAR(50),
    customer_unique_id VARCHAR(50),
    customer_zip_code_prefix VARCHAR(10),
    customer_city VARCHAR(100),
    customer_state VARCHAR(5)
);

DROP TABLE IF EXISTS staging.stg_sellers CASCADE;
CREATE TABLE staging.stg_sellers (
    seller_id VARCHAR(50),
    seller_zip_code_prefix VARCHAR(10),
    seller_city VARCHAR(100),
    seller_state VARCHAR(5)
);

DROP TABLE IF EXISTS staging.stg_products CASCADE;
CREATE TABLE staging.stg_products (
    product_id VARCHAR(50),
    product_category_name VARCHAR(100),
    product_name_lenght NUMERIC(10, 2),
    product_description_lenght NUMERIC(10, 2),
    product_photos_qty NUMERIC(10, 2),
    product_weight_g NUMERIC(12, 2),
    product_length_cm NUMERIC(10, 2),
    product_height_cm NUMERIC(10, 2),
    product_width_cm NUMERIC(10, 2)
);

DROP TABLE IF EXISTS staging.stg_geolocation CASCADE;
CREATE TABLE staging.stg_geolocation (
    geolocation_zip_code_prefix VARCHAR(10),
    geolocation_lat NUMERIC(15, 10),
    geolocation_lng NUMERIC(15, 10),
    geolocation_city VARCHAR(100),
    geolocation_state VARCHAR(5)
);

DROP TABLE IF EXISTS staging.stg_category_translation CASCADE;
CREATE TABLE staging.stg_category_translation (
    product_category_name VARCHAR(100),
    product_category_name_english VARCHAR(100)
);