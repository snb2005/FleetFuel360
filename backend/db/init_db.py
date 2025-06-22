"""
Database Initialization Script
Creates tables and populates with sample data from CSV
"""

import os
import sys
import csv
import psycopg2
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def create_database_if_not_exists():
    """Create the FleetFuel360 database if it doesn't exist"""
    
    # Connect to PostgreSQL without specifying database
    conn_str = f"postgresql://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/postgres"
    
    try:
        engine = create_engine(conn_str, isolation_level='AUTOCOMMIT')
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(
                "SELECT 1 FROM pg_database WHERE datname = :db_name"
            ), {"db_name": Config.POSTGRES_DB})
            
            if not result.fetchone():
                conn.execute(text(f"CREATE DATABASE {Config.POSTGRES_DB}"))
                print(f"✅ Created database: {Config.POSTGRES_DB}")
            else:
                print(f"✅ Database {Config.POSTGRES_DB} already exists")
                
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    return True

def execute_schema():
    """Execute the SQL schema file to create tables"""
    
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        with open(schema_path, 'r') as schema_file:
            schema_sql = schema_file.read()
        
        with engine.connect() as conn:
            # Execute schema in a transaction
            trans = conn.begin()
            try:
                conn.execute(text(schema_sql))
                trans.commit()
                print("✅ Schema executed successfully")
            except Exception as e:
                trans.rollback()
                raise e
                
    except Exception as e:
        print(f"❌ Error executing schema: {e}")
        return False
    
    return True

def load_csv_data():
    """Load sample fuel logs data from CSV file"""
    
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
        'data', 'fuel_logs_sample.csv'
    )
    
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        with open(csv_path, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            with engine.connect() as conn:
                trans = conn.begin()
                try:
                    # Clear existing fuel logs
                    conn.execute(text("DELETE FROM fuel_logs"))
                    
                    # Insert new data
                    for row in csv_reader:
                        conn.execute(text("""
                            INSERT INTO fuel_logs (vehicle_id, timestamp, km_driven, fuel_used)
                            VALUES (:vehicle_id, :timestamp, :km_driven, :fuel_used)
                        """), {
                            'vehicle_id': row['vehicle_id'],
                            'timestamp': datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S'),
                            'km_driven': float(row['km_driven']),
                            'fuel_used': float(row['fuel_used'])
                        })
                    
                    trans.commit()
                    print("✅ CSV data loaded successfully")
                    
                except Exception as e:
                    trans.rollback()
                    raise e
                    
    except Exception as e:
        print(f"❌ Error loading CSV data: {e}")
        return False
    
    return True

def verify_data():
    """Verify that data was loaded correctly"""
    
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        with engine.connect() as conn:
            # Count vehicles
            vehicle_count = conn.execute(text("SELECT COUNT(*) FROM vehicles")).scalar()
            print(f"✅ Vehicles in database: {vehicle_count}")
            
            # Count fuel logs
            log_count = conn.execute(text("SELECT COUNT(*) FROM fuel_logs")).scalar()
            print(f"✅ Fuel logs in database: {log_count}")
            
            # Show sample data
            result = conn.execute(text("""
                SELECT vehicle_id, COUNT(*) as log_count, 
                       AVG(fuel_efficiency) as avg_efficiency
                FROM fuel_logs 
                GROUP BY vehicle_id 
                ORDER BY vehicle_id
            """))
            
            print("\n📊 Sample Statistics:")
            print("Vehicle ID | Log Count | Avg Efficiency (km/L)")
            print("-" * 50)
            for row in result:
                print(f"{row[0]:<10} | {row[1]:<9} | {row[2]:.2f}")
                
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
        return False
    
    return True

def main():
    """Main initialization function"""
    
    print("🚀 Initializing FleetFuel360 Database...")
    print("-" * 50)
    
    # Step 1: Create database
    if not create_database_if_not_exists():
        print("❌ Failed to create database. Exiting.")
        sys.exit(1)
    
    # Step 2: Execute schema
    if not execute_schema():
        print("❌ Failed to execute schema. Exiting.")
        sys.exit(1)
    
    # Step 3: Load CSV data
    if not load_csv_data():
        print("❌ Failed to load CSV data. Exiting.")
        sys.exit(1)
    
    # Step 4: Verify data
    if not verify_data():
        print("❌ Failed to verify data. Exiting.")
        sys.exit(1)
    
    print("\n🎉 Database initialization completed successfully!")
    print("You can now run the Flask application with: python app.py")

if __name__ == "__main__":
    main()
