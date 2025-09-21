CREATE DATABASE IF NOT EXISTS pizzadb;
USE pizzadb;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'customer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pizzas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category VARCHAR(50),
    size VARCHAR(20)
);
-- Orders table (one per checkout)
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    delivery_fee DECIMAL(10,2) NOT NULL DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(50),
    payment_status VARCHAR(50) DEFAULT 'unpaid',
    contact_number VARCHAR(20) NOT NULL,
    address VARCHAR(255),
    reward VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items table (all pizzas in that order)
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    pizza_id INT NOT NULL,
    size VARCHAR(10),
    crust VARCHAR(50),
    cheese VARCHAR(50),
    toppings TEXT,
    extras VARCHAR(100),
    quantity INT DEFAULT 1,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pizza_id INT NOT NULL,
    quantity INT DEFAULT 1,
    size VARCHAR(10) NOT NULL DEFAULT 'small',
    unit_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    toppings TEXT,
    extras TEXT,
    crust VARCHAR(50) DEFAULT 'regular',
    cheese VARCHAR(50) DEFAULT 'normal',
    toppings_hash VARCHAR(32) GENERATED ALWAYS AS (MD5(IFNULL(toppings,''))) STORED,
    extras_hash VARCHAR(32) GENERATED ALWAYS AS (MD5(IFNULL(extras,''))) STORED,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pizza_id) REFERENCES pizzas(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS order_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    status VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

CREATE TABLE IF NOT EXISTS spin_rewards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    reward VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
