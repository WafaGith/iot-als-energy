CREATE DATABASE IF NOT EXISTS als_energy;
USE als_energy;

CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS sensor_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    mesin_id INT NOT NULL,
    volt FLOAT,
    arus FLOAT,
    daya FLOAT,
    energi FLOAT,
    frekuensi FLOAT,
    pf FLOAT
);

CREATE TABLE IF NOT EXISTS system_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(100),
    description TEXT
);

CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    message TEXT,
    status VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS settings (
    setting_key VARCHAR(50) PRIMARY KEY,
    setting_value TEXT
);

-- Insert default admin (username: admin, password: admin_password)
-- Hasher from werkzeug.security will be used for actual password checking, but here's a default plain insert for testing which we will hash in Python immediately if empty.
-- Better yet, we can handle default admin creation in python if table is empty.

-- Insert default settings
INSERT IGNORE INTO settings (setting_key, setting_value) VALUES 
('tarif_per_kwh', '1444.70');
