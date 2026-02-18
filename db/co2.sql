-- --------------------------------------------------------
-- CO2NECT DATABASE (MySQL 5.0 Compatible Version)
-- --------------------------------------------------------

DROP DATABASE IF EXISTS co2nect;
CREATE DATABASE co2nect CHARACTER SET utf8;
USE co2nect;

-- ========================================================
-- FARMER TABLE
-- ========================================================
CREATE TABLE farmer (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    city VARCHAR(100),
    address TEXT,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY unique_farmer_email (email),
    UNIQUE KEY unique_farmer_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


-- ========================================================
-- CONSUMER TABLE
-- ========================================================
CREATE TABLE consumer (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    city VARCHAR(100),
    address TEXT,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY unique_consumer_email (email),
    UNIQUE KEY unique_consumer_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


-- ========================================================
-- INDUSTRIAL TABLE
-- ========================================================
CREATE TABLE industrial (
    id INT NOT NULL AUTO_INCREMENT,
    company_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    city VARCHAR(100),
    address TEXT,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY unique_industrial_email (email),
    UNIQUE KEY unique_industrial_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


-- ========================================================
-- ALGAE GROWTH TABLE
-- ========================================================
CREATE TABLE algaegrowth (
    id INT NOT NULL AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    algae_kg DECIMAL(10,2) NOT NULL,
    co2_tons DECIMAL(10,4) NOT NULL,
    credits DECIMAL(10,4) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_algaegrowth_farmer (farmer_id),
    CONSTRAINT fk_algaegrowth_farmer
        FOREIGN KEY (farmer_id)
        REFERENCES farmer(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


-- ========================================================
-- PRODUCTS TABLE
-- ========================================================
CREATE TABLE products (
    id INT NOT NULL AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    image VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_products_farmer (farmer_id),
    CONSTRAINT fk_products_farmer
        FOREIGN KEY (farmer_id)
        REFERENCES farmer(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


-- ========================================================
-- CART TABLE
-- ========================================================
CREATE TABLE cart (
    id INT NOT NULL AUTO_INCREMENT,
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY unique_cart_item (customer_id, product_id),
    KEY idx_cart_customer (customer_id),
    KEY idx_cart_product (product_id),
    CONSTRAINT fk_cart_consumer
        FOREIGN KEY (customer_id)
        REFERENCES consumer(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_cart_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


-- ========================================================
-- PURCHASES TABLE
-- ========================================================
CREATE TABLE purchases (
    id INT NOT NULL AUTO_INCREMENT,
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_purchase_customer (customer_id),
    KEY idx_purchase_product (product_id),
    CONSTRAINT fk_purchase_consumer
        FOREIGN KEY (customer_id)
        REFERENCES consumer(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_purchase_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


-- ========================================================
-- TRANSACTIONS TABLE
-- ========================================================
CREATE TABLE transactions (
    id INT NOT NULL AUTO_INCREMENT,
    industrialist_id INT NOT NULL,transactions
    farmer_id INT NOT NULL,
    algaegrowth_id INT NOT NULL,
    credits DECIMAL(10,4) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_transaction_industrial (industrialist_id),
    KEY idx_transaction_farmer (farmer_id),
    KEY idx_transaction_algae (algaegrowth_id),
    CONSTRAINT fk_transaction_industrial
        FOREIGN KEY (industrialist_id)
        REFERENCES industrial(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_transaction_farmer
        FOREIGN KEY (farmer_id)
        REFERENCES farmer(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_transaction_algae
        FOREIGN KEY (algaegrowth_id)
        REFERENCES algaegrowth(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
