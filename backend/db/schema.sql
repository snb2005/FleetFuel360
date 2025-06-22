-- FleetFuel360 Database Schema
-- PostgreSQL database schema for fuel efficiency tracking

-- Drop existing tables if they exist
DROP TABLE IF EXISTS fuel_logs CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;

-- Create vehicles table
CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(20) UNIQUE NOT NULL,
    make VARCHAR(50),
    model VARCHAR(50),
    year INTEGER,
    fuel_capacity DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create fuel_logs table
CREATE TABLE fuel_logs (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    km_driven DECIMAL(8,2) NOT NULL,
    fuel_used DECIMAL(6,2) NOT NULL,
    fuel_efficiency DECIMAL(6,2) GENERATED ALWAYS AS (
        CASE 
            WHEN fuel_used > 0 THEN km_driven / fuel_used 
            ELSE 0 
        END
    ) STORED,
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_score DECIMAL(6,4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX idx_fuel_logs_vehicle_id ON fuel_logs(vehicle_id);
CREATE INDEX idx_fuel_logs_timestamp ON fuel_logs(timestamp);
CREATE INDEX idx_fuel_logs_is_anomaly ON fuel_logs(is_anomaly);

-- Insert sample vehicles
INSERT INTO vehicles (vehicle_id, make, model, year, fuel_capacity) VALUES
('TRUCK001', 'Volvo', 'VNL 760', 2022, 300.00),
('TRUCK002', 'Freightliner', 'Cascadia', 2021, 280.00),
('TRUCK003', 'Peterbilt', '579', 2023, 320.00),
('TRUCK004', 'Kenworth', 'T680', 2022, 290.00),
('TRUCK005', 'Mack', 'Anthem', 2021, 310.00);
