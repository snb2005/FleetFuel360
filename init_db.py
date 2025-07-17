"""
Database initialization script for FleetFuel360
Creates MySQL database, tables, indexes, and sample data
"""

import mysql.connector
from mysql.connector import Error
import sys

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',  # Change this to your MySQL password
    'charset': 'utf8mb4'
}

def create_database_and_tables():
    """Create database, tables, and indexes"""
    
    # SQL statements for database setup
    create_database_sql = "CREATE DATABASE IF NOT EXISTS fleetfuel360 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    
    use_database_sql = "USE fleetfuel360"
    
    # Create vehicles table
    create_vehicles_table = """
    CREATE TABLE IF NOT EXISTS vehicles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        type VARCHAR(50) NOT NULL,
        license_plate VARCHAR(20) DEFAULT '',
        year INT DEFAULT NULL,
        make VARCHAR(50) DEFAULT '',
        model VARCHAR(50) DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_vehicle_type (type),
        INDEX idx_vehicle_name (name)
    ) ENGINE=InnoDB
    """
    
    # Create fuel_logs table with foreign key constraint
    create_fuel_logs_table = """
    CREATE TABLE IF NOT EXISTS fuel_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        vehicle_id INT NOT NULL,
        log_date DATE NOT NULL,
        km_driven FLOAT NOT NULL,
        fuel_used FLOAT NOT NULL,
        cost DECIMAL(10,2) DEFAULT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
        INDEX idx_fuel_logs_vehicle_id (vehicle_id),
        INDEX idx_fuel_logs_date (log_date),
        INDEX idx_fuel_logs_efficiency (km_driven, fuel_used)
    ) ENGINE=InnoDB
    """
    
    # Sample data for vehicles
    insert_vehicles_sql = """
    INSERT INTO vehicles (name, type, license_plate, year, make, model) VALUES
    ('Fleet Van 001', 'Van', 'ABC-123', 2020, 'Ford', 'Transit'),
    ('Delivery Truck 001', 'Truck', 'DEF-456', 2019, 'Isuzu', 'NPR'),
    ('Company Car 001', 'Car', 'GHI-789', 2021, 'Toyota', 'Camry'),
    ('Fleet Van 002', 'Van', 'JKL-012', 2020, 'Ford', 'Transit'),
    ('Delivery Truck 002', 'Truck', 'MNO-345', 2018, 'Isuzu', 'NPR'),
    ('Company Car 002', 'Car', 'PQR-678', 2022, 'Honda', 'Accord')
    ON DUPLICATE KEY UPDATE id=id
    """
    
    # Sample data for fuel logs
    insert_fuel_logs_sql = """
    INSERT INTO fuel_logs (vehicle_id, log_date, km_driven, fuel_used, cost, notes) VALUES
    (1, '2024-01-15', 145.2, 18.5, 32.50, 'Regular maintenance route'),
    (1, '2024-01-22', 167.8, 21.2, 37.20, 'Long distance delivery'),
    (1, '2024-01-29', 132.4, 16.8, 29.40, 'City deliveries'),
    (2, '2024-01-16', 89.3, 15.6, 27.30, 'Heavy load transport'),
    (2, '2024-01-23', 92.7, 16.2, 28.35, 'Construction site delivery'),
    (2, '2024-01-30', 76.5, 13.8, 24.15, 'Local pickup'),
    (3, '2024-01-17', 234.6, 19.2, 33.60, 'Business trip'),
    (3, '2024-01-24', 187.9, 15.4, 26.95, 'Client meetings'),
    (3, '2024-01-31', 198.5, 16.3, 28.53, 'Conference attendance'),
    (4, '2024-01-18', 156.3, 19.8, 34.65, 'Mixed route'),
    (4, '2024-01-25', 143.7, 18.2, 31.85, 'Standard delivery'),
    (5, '2024-01-19', 87.4, 15.9, 27.83, 'Construction materials'),
    (5, '2024-01-26', 94.2, 17.1, 29.93, 'Equipment transport'),
    (6, '2024-01-20', 267.8, 21.5, 37.63, 'Long business trip'),
    (6, '2024-01-27', 198.2, 16.7, 29.23, 'Multiple client visits'),
    -- Additional recent entries for better ML training
    (1, '2024-02-05', 152.8, 19.3, 33.83, 'Weekly route'),
    (1, '2024-02-12', 148.6, 18.9, 33.08, 'Regular delivery'),
    (2, '2024-02-06', 91.5, 16.8, 29.40, 'Construction delivery'),
    (3, '2024-02-07', 245.3, 20.1, 35.18, 'Regional meeting'),
    (4, '2024-02-08', 159.7, 20.2, 35.35, 'Extended route'),
    (5, '2024-02-09', 88.9, 15.7, 27.48, 'Materials pickup'),
    (6, '2024-02-10', 189.4, 15.8, 27.65, 'Client visits'),
    -- Add some anomalous data points for testing
    (1, '2024-02-13', 45.2, 25.8, 45.15, 'Unusual high fuel usage - investigate'),
    (2, '2024-02-14', 125.6, 8.2, 14.35, 'Unusually efficient - possible error'),
    (3, '2024-02-15', 289.7, 35.4, 61.95, 'Extremely high consumption - check vehicle')
    ON DUPLICATE KEY UPDATE id=id
    """
    
    try:
        # Connect to MySQL server (without database)
        print("Connecting to MySQL server...")
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Create database
        print("Creating database...")
        cursor.execute(create_database_sql)
        
        # Use the database
        cursor.execute(use_database_sql)
        
        # Create tables
        print("Creating vehicles table...")
        cursor.execute(create_vehicles_table)
        
        print("Creating fuel_logs table...")
        cursor.execute(create_fuel_logs_table)
        
        # Insert sample data
        print("Inserting sample vehicles...")
        cursor.execute(insert_vehicles_sql)
        
        print("Inserting sample fuel logs...")
        cursor.execute(insert_fuel_logs_sql)
        
        # Commit changes
        connection.commit()
        
        print("✅ Database initialization completed successfully!")
        print("Database: fleetfuel360")
        print("Tables created: vehicles, fuel_logs")
        print("Sample data inserted: 6 vehicles, 25 fuel logs")
        
        # Show table info
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        vehicle_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM fuel_logs")
        log_count = cursor.fetchone()[0]
        
        print(f"Final counts: {vehicle_count} vehicles, {log_count} fuel logs")
        
    except Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Database connection closed.")

def show_database_info():
    """Show information about the created database"""
    try:
        config = DB_CONFIG.copy()
        config['database'] = 'fleetfuel360'
        
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        print("\n" + "="*50)
        print("DATABASE INFORMATION")
        print("="*50)
        
        # Show tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"Tables: {[table[0] for table in tables]}")
        
        # Show vehicles table structure
        print("\nVEHICLES TABLE:")
        cursor.execute("DESCRIBE vehicles")
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[1]})")
        
        # Show fuel_logs table structure
        print("\nFUEL_LOGS TABLE:")
        cursor.execute("DESCRIBE fuel_logs")
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[1]})")
        
        # Show indexes
        print("\nINDEXES:")
        cursor.execute("SHOW INDEX FROM vehicles")
        for row in cursor.fetchall():
            print(f"  vehicles.{row[4]} ({row[2]})")
            
        cursor.execute("SHOW INDEX FROM fuel_logs")
        for row in cursor.fetchall():
            print(f"  fuel_logs.{row[4]} ({row[2]})")
        
        # Sample data preview
        print("\nSAMPLE DATA:")
        cursor.execute("SELECT name, type FROM vehicles LIMIT 3")
        vehicles = cursor.fetchall()
        for vehicle in vehicles:
            print(f"  Vehicle: {vehicle[0]} ({vehicle[1]})")
        
        cursor.execute("""
            SELECT v.name, fl.log_date, fl.km_driven, fl.fuel_used,
                   ROUND(fl.km_driven/fl.fuel_used, 2) as efficiency
            FROM fuel_logs fl
            JOIN vehicles v ON fl.vehicle_id = v.id
            ORDER BY fl.log_date DESC
            LIMIT 3
        """)
        logs = cursor.fetchall()
        for log in logs:
            print(f"  Log: {log[0]} on {log[1]} - {log[2]}km, {log[3]}L (eff: {log[4]})")
        
    except Error as e:
        print(f"Error showing database info: {e}")
    
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    print("FleetFuel360 Database Initialization")
    print("="*40)
    
    # Check if MySQL credentials need to be updated
    if DB_CONFIG['password'] == 'password':
        print("⚠️  WARNING: Please update the MySQL password in this script!")
        print("   Edit DB_CONFIG['password'] with your actual MySQL root password")
        print()
        
        response = input("Continue with default password? (y/N): ")
        if response.lower() != 'y':
            print("Please update the password and run again.")
            sys.exit(1)
    
    create_database_and_tables()
    show_database_info()
    
    print("\n" + "="*50)
    print("NEXT STEPS:")
    print("="*50)
    print("1. Update app.py with your MySQL credentials")
    print("2. Install requirements: pip install -r requirements.txt")
    print("3. Run the application: python app.py")
    print("4. Test the API endpoints (see README.md)")
