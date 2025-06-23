# 🗄️ FleetFuel360 Database Guide

## Database Architecture Overview

FleetFuel360 uses **PostgreSQL** as its primary database, chosen for its reliability, performance, and excellent support for analytical workloads.

### Database Schema

```sql
-- Vehicles table: Fleet vehicle registry
CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) UNIQUE NOT NULL,  -- Business key (TRUCK001, etc.)
    model VARCHAR(100),                      -- Vehicle model
    year INTEGER,                           -- Manufacturing year
    fuel_type VARCHAR(50),                  -- Diesel, Gasoline, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fuel logs table: Fuel consumption records
CREATE TABLE fuel_logs (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(50) REFERENCES vehicles(vehicle_id),
    timestamp TIMESTAMP NOT NULL,           -- When fuel was logged
    km_driven DECIMAL(10,2),               -- Distance driven (km)
    fuel_used DECIMAL(10,2),               -- Fuel consumed (liters)
    fuel_efficiency DECIMAL(10,2),         -- Calculated km/L
    is_anomaly BOOLEAN DEFAULT FALSE,       -- ML anomaly flag
    anomaly_score DECIMAL(10,4),           -- ML anomaly score (-1 to 1)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_fuel_logs_vehicle_id ON fuel_logs(vehicle_id);
CREATE INDEX idx_fuel_logs_timestamp ON fuel_logs(timestamp);
CREATE INDEX idx_fuel_logs_anomaly ON fuel_logs(is_anomaly);
```

## Render.com Database Configuration

### 1. Managed PostgreSQL Service

Render automatically provisions and manages your PostgreSQL database:

```yaml
# render.yaml - Database service configuration
- type: pserv
  name: fleetfuel360-db
  plan: free                    # Free tier: 1GB storage
  databaseName: fleetfuel360   # Database name
  databaseUser: fleetfuel_user # Database user
```

### 2. Automatic Environment Variables

Render injects these database connection variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_HOST` | Database hostname | `dpg-xxx-a.oregon-postgres.render.com` |
| `POSTGRES_PORT` | Database port | `5432` |
| `POSTGRES_DB` | Database name | `fleetfuel360` |
| `POSTGRES_USER` | Database username | `fleetfuel_user` | 
| `POSTGRES_PASSWORD` | Database password | `auto-generated-secure-password` |

### 3. Connection String

The application automatically constructs the connection string:
```python
# backend/config.py
SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
```

## Database Initialization Process

### 1. Build-Time Initialization

The `build.sh` script runs during deployment:

```bash
#!/usr/bin/env bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "
from backend.db.init_db import initialize_database
initialize_database()
"
```

### 2. Database Setup Steps

1. **Schema Creation**: Creates tables if they don't exist
2. **Sample Data Loading**: Loads CSV data for demo/testing
3. **Index Creation**: Adds performance indexes
4. **Data Verification**: Confirms successful setup

### 3. Sample Data Populated

**Vehicles** (5 sample trucks):
```
TRUCK001 - Volvo FH16 2020 (Diesel)
TRUCK002 - Mercedes Actros 2019 (Diesel)  
TRUCK003 - Scania R500 2021 (Diesel)
TRUCK004 - MAN TGX 2018 (Diesel)
TRUCK005 - Iveco Stralis 2020 (Diesel)
```

**Fuel Logs** (50+ records):
- Realistic fuel consumption data
- Calculated efficiency metrics (km/L)
- Time-series data over 30+ days
- Some records flagged as anomalies for ML testing

## Database Health Monitoring

### 1. Health Check API

```bash
# Basic health check
GET /api/health
{
  "status": "healthy",
  "database": {
    "status": "healthy",
    "vehicle_count": 5,
    "log_count": 56
  }
}

# Detailed database status  
GET /api/db-status
{
  "status": "healthy",
  "message": "Database is accessible and populated",
  "tables": ["vehicles", "fuel_logs"],
  "vehicle_count": 5,
  "log_count": 56
}
```

### 2. Database Monitoring

**Render Dashboard**:
- Connection count
- Storage usage
- Query performance
- Backup status

**Application Monitoring**:
- Connection pool status
- Query execution times
- Error rates
- Data integrity checks

## Production Database Management

### 1. Accessing Production Database

**Via Render Dashboard**:
1. Go to your database service
2. Click "Connect" tab
3. Use provided connection details

**Command Line Access**:
```bash
# Use connection details from Render dashboard
psql "postgresql://user:password@host:port/database"

# Example queries
\dt                              -- List tables
SELECT COUNT(*) FROM vehicles;   -- Count vehicles
SELECT COUNT(*) FROM fuel_logs;  -- Count fuel logs

-- Sample data inspection
SELECT vehicle_id, model, fuel_type FROM vehicles;
SELECT vehicle_id, km_driven, fuel_used, fuel_efficiency 
FROM fuel_logs ORDER BY timestamp DESC LIMIT 10;
```

### 2. Database Maintenance

**Automatic Features**:
- Daily backups (7-day retention on free tier)
- SSL/TLS encryption
- Connection pooling
- Query optimization

**Manual Maintenance**:
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('fleetfuel360'));

-- Check table sizes
SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(tablename::text))
FROM pg_tables WHERE schemaname = 'public';

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM fuel_logs WHERE vehicle_id = 'TRUCK001';

-- Update statistics for query planner
ANALYZE vehicles;
ANALYZE fuel_logs;
```

### 3. Backup and Recovery

**Automatic Backups**:
- Daily automatic backups
- 7-day retention (free tier)
- Point-in-time recovery available
- Restore via Render dashboard

**Manual Backup**:
```bash
# Export database (use Render connection details)
pg_dump "postgresql://user:pass@host:port/db" > fleetfuel360_backup.sql

# Restore from backup
psql "postgresql://user:pass@host:port/db" < fleetfuel360_backup.sql
```

## Database Performance Optimization

### 1. Indexing Strategy

```sql
-- Primary indexes (automatically created)
CREATE INDEX idx_fuel_logs_vehicle_id ON fuel_logs(vehicle_id);
CREATE INDEX idx_fuel_logs_timestamp ON fuel_logs(timestamp);

-- Composite indexes for common queries
CREATE INDEX idx_fuel_logs_vehicle_timestamp ON fuel_logs(vehicle_id, timestamp);
CREATE INDEX idx_fuel_logs_anomaly_score ON fuel_logs(is_anomaly, anomaly_score);
```

### 2. Query Optimization

```sql
-- Efficient vehicle statistics query
SELECT 
    vehicle_id,
    COUNT(*) as total_logs,
    AVG(fuel_efficiency) as avg_efficiency,
    MAX(timestamp) as last_log
FROM fuel_logs 
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY vehicle_id;

-- Anomaly detection query
SELECT vehicle_id, timestamp, fuel_efficiency, anomaly_score
FROM fuel_logs 
WHERE is_anomaly = true 
ORDER BY anomaly_score DESC;
```

### 3. Connection Management

```python
# SQLAlchemy connection pooling (configured in app)
engine = create_engine(
    DATABASE_URI,
    pool_size=10,           # Connection pool size
    pool_timeout=30,        # Timeout for getting connection
    pool_recycle=3600,      # Recycle connections every hour
    echo=False              # Disable SQL logging in production
)
```

## Troubleshooting Database Issues

### 1. Connection Problems

**Symptoms**: App can't connect to database
**Solutions**:
- Check Render dashboard for database service status
- Verify environment variables are set correctly
- Wait 2-3 minutes for database service to fully start
- Check build logs for initialization errors

### 2. Data Not Loading

**Symptoms**: Empty tables or missing data
**Solutions**:
- Check build logs for CSV loading errors
- Verify sample data files exist in `/data` directory
- Run manual database initialization
- Check file permissions and paths

### 3. Performance Issues

**Symptoms**: Slow API responses
**Solutions**:
- Add appropriate indexes
- Optimize queries with EXPLAIN ANALYZE
- Upgrade to higher tier plan for more resources
- Implement application-level caching

### 4. Schema Changes

**For Development**:
```bash
# Drop and recreate tables (WARNING: DATA LOSS)
python -c "
from backend.db.init_db import execute_schema
execute_schema()
"
```

**For Production**:
- Create database migration scripts
- Test migrations on staging first
- Consider downtime or rolling updates
- Always backup before schema changes

## Database Security

### 1. Access Control

- Database user has minimal required permissions
- No direct public access to database
- SSL/TLS encryption for all connections
- Environment variables for sensitive data

### 2. Data Protection

- Regular automated backups
- Encrypted connections
- Secure credential management
- No hardcoded passwords

### 3. SQL Injection Prevention

- SQLAlchemy ORM with parameterized queries
- Input validation and sanitization
- No dynamic SQL construction
- Prepared statements for all queries

---

This database setup provides a robust foundation for the FleetFuel360 application with automatic provisioning, monitoring, and maintenance through Render's managed PostgreSQL service.
