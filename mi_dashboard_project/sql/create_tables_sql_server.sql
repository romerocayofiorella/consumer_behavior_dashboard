CREATE DATABASE consumer_behavior;
GO

USE consumer_behavior;
GO

-- =====================
-- DIMENSION TABLES
-- =====================

CREATE TABLE dim_gender (
    gender_id INT IDENTITY(1,1) PRIMARY KEY,
    gender_name VARCHAR(50) NOT NULL
);
GO

CREATE TABLE dim_location (
    location_id INT IDENTITY(1,1) PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL
);
GO

CREATE TABLE dim_item (
    item_id INT IDENTITY(1,1) PRIMARY KEY,
    item_name VARCHAR(100) NOT NULL
);
GO

CREATE TABLE dim_category (
    category_id INT IDENTITY(1,1) PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL
);
GO

CREATE TABLE dim_size (
    size_id INT IDENTITY(1,1) PRIMARY KEY,
    size_name VARCHAR(50) NOT NULL
);
GO

CREATE TABLE dim_color (
    color_id INT IDENTITY(1,1) PRIMARY KEY,
    color_name VARCHAR(50) NOT NULL
);
GO

CREATE TABLE dim_season (
    season_id INT IDENTITY(1,1) PRIMARY KEY,
    season_name VARCHAR(50) NOT NULL
);
GO

CREATE TABLE dim_subscription_status (
    subscription_status_id INT IDENTITY(1,1) PRIMARY KEY,
    subscription_status_name VARCHAR(10) NOT NULL
);
GO

CREATE TABLE dim_shipping_type (
    shipping_type_id INT IDENTITY(1,1) PRIMARY KEY,
    shipping_type_name VARCHAR(50) NOT NULL
);
GO

CREATE TABLE dim_discount_status (
    discount_status_id INT IDENTITY(1,1) PRIMARY KEY,
    discount_status_name VARCHAR(10) NOT NULL
);
GO

CREATE TABLE dim_promo_status (
    promo_status_id INT IDENTITY(1,1) PRIMARY KEY,
    promo_status_name VARCHAR(10) NOT NULL
);
GO

CREATE TABLE dim_payment_method (
    payment_method_id INT IDENTITY(1,1) PRIMARY KEY,
    payment_method_name VARCHAR(50) NOT NULL
);
GO

CREATE TABLE dim_frequency (
    frequency_id INT IDENTITY(1,1) PRIMARY KEY,
    frequency_name VARCHAR(50) NOT NULL
);
GO

-- =====================
-- PRODUCT TABLE
-- =====================

CREATE TABLE dim_product (
    product_id INT IDENTITY(1,1) PRIMARY KEY,
    item_id INT NOT NULL,
    category_id INT NOT NULL,
    size_id INT NOT NULL,
    color_id INT NOT NULL,

    CONSTRAINT FK_product_item
        FOREIGN KEY (item_id)
        REFERENCES dim_item(item_id),

    CONSTRAINT FK_product_category
        FOREIGN KEY (category_id)
        REFERENCES dim_category(category_id),

    CONSTRAINT FK_product_size
        FOREIGN KEY (size_id)
        REFERENCES dim_size(size_id),

    CONSTRAINT FK_product_color
        FOREIGN KEY (color_id)
        REFERENCES dim_color(color_id)
);
GO

-- =====================
-- CUSTOMER TABLE
-- =====================

CREATE TABLE dim_customer (
    customer_id INT PRIMARY KEY,
    birth_year INT NOT NULL,
    gender_id INT NOT NULL,
    location_id INT NOT NULL,

    CONSTRAINT FK_customer_gender
        FOREIGN KEY (gender_id)
        REFERENCES dim_gender(gender_id),

    CONSTRAINT FK_customer_location
        FOREIGN KEY (location_id)
        REFERENCES dim_location(location_id)
);
GO

-- =====================
-- FACT TABLE
-- =====================

CREATE TABLE fact_transactions (
    transaction_id INT IDENTITY(1,1) PRIMARY KEY,

    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    season_id INT NOT NULL,
    subscription_status_id INT NOT NULL,
    shipping_type_id INT NOT NULL,
    discount_status_id INT NOT NULL,
    promo_status_id INT NOT NULL,
    payment_method_id INT NOT NULL,
    frequency_id INT NOT NULL,

    purchase_amount_usd DECIMAL(10,2) NOT NULL,
    previous_purchases INT NOT NULL,
    review_rating INT NOT NULL,

    CONSTRAINT FK_fact_customer
        FOREIGN KEY (customer_id)
        REFERENCES dim_customer(customer_id),

    CONSTRAINT FK_fact_product
        FOREIGN KEY (product_id)
        REFERENCES dim_product(product_id),

    CONSTRAINT FK_fact_season
        FOREIGN KEY (season_id)
        REFERENCES dim_season(season_id),

    CONSTRAINT FK_fact_subscription_status
        FOREIGN KEY (subscription_status_id)
        REFERENCES dim_subscription_status(subscription_status_id),

    CONSTRAINT FK_fact_shipping_type
        FOREIGN KEY (shipping_type_id)
        REFERENCES dim_shipping_type(shipping_type_id),

    CONSTRAINT FK_fact_discount_status
        FOREIGN KEY (discount_status_id)
        REFERENCES dim_discount_status(discount_status_id),

    CONSTRAINT FK_fact_promo_status
        FOREIGN KEY (promo_status_id)
        REFERENCES dim_promo_status(promo_status_id),

    CONSTRAINT FK_fact_payment_method
        FOREIGN KEY (payment_method_id)
        REFERENCES dim_payment_method(payment_method_id),

    CONSTRAINT FK_fact_frequency
        FOREIGN KEY (frequency_id)
        REFERENCES dim_frequency(frequency_id)
);
GO