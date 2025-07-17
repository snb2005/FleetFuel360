# FleetFuel360 - Simplified Fuel Analytics Backend

A Flask-based REST API for vehicle fleet management and fuel analytics with basic machine learning integration. This project demonstrates backend development skills with MySQL database operations, RESTful API design, and simple ML models for fuel consumption prediction and anomaly detection.

## 🚀 Technologies Used

- **Backend**: Python 3.8+, Flask 2.3.3
- **Database**: MySQL 8.0+ with InnoDB engine
- **Machine Learning**: scikit-learn (Linear Regression, Isolation Forest)
- **Data Processing**: NumPy, Pandas
- **Database Connector**: mysql-connector-python

## 📋 Project Overview

FleetFuel360 provides a clean, educational backend for managing vehicle fleets and analyzing fuel consumption patterns. Key features include:

- **RESTful API**: Complete CRUD operations for vehicles and fuel logs
- **Database Design**: Optimized MySQL schema with proper indexing and foreign key constraints
- **Machine Learning**: Fuel consumption prediction and anomaly detection
- **Statistics**: Aggregate KPIs and per-vehicle analytics
- **Error Handling**: Comprehensive error responses and logging

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.8 or higher
- MySQL 8.0 or higher
- pip (Python package manager)

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd FleetFuel360
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure MySQL credentials**:
   - Update the `DB_CONFIG` in both `app.py` and `init_db.py`
   - Replace `'password': 'password'` with your actual MySQL root password

5. **Initialize the database**:
   ```bash
   python init_db.py
   ```

6. **Run the application**:
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:5000`

## 📊 Database Schema

### Vehicles Table
```sql
CREATE TABLE vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    license_plate VARCHAR(20) DEFAULT '',
    year INT DEFAULT NULL,
    make VARCHAR(50) DEFAULT '',
    model VARCHAR(50) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Fuel Logs Table
```sql
CREATE TABLE fuel_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    log_date DATE NOT NULL,
    km_driven FLOAT NOT NULL,
    fuel_used FLOAT NOT NULL,
    cost DECIMAL(10,2) DEFAULT NULL,
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);
```

### Key Indexes
- `idx_fuel_logs_vehicle_id` on `fuel_logs.vehicle_id` (foreign key index for fast JOINs)
- `idx_fuel_logs_date` on `fuel_logs.log_date` (for date-based queries)
- `idx_fuel_logs_efficiency` on `(km_driven, fuel_used)` (for efficiency calculations)

## 🔌 API Reference

### Vehicle Endpoints

#### GET /vehicles
Get all vehicles with optional filtering.

**Query Parameters:**
- `type` (optional): Filter by vehicle type

**Response:**
```json
{
  "vehicles": [
    {
      "id": 1,
      "name": "Fleet Van 001",
      "type": "Van",
      "license_plate": "ABC-123",
      "year": 2020,
      "make": "Ford",
      "model": "Transit"
    }
  ],
  "count": 1
}
```

#### POST /vehicles
Add a new vehicle.

**Request Body:**
```json
{
  "name": "Fleet Van 003",
  "type": "Van",
  "license_plate": "XYZ-789",
  "year": 2023,
  "make": "Ford",
  "model": "Transit"
}
```

**Response:**
```json
{
  "message": "Vehicle added successfully",
  "vehicle_id": 7
}
```

#### GET /vehicles/{id}
Get a specific vehicle by ID.

#### PUT /vehicles/{id}
Update a vehicle's information.

#### DELETE /vehicles/{id}
Delete a vehicle and all associated fuel logs.

### Fuel Log Endpoints

#### GET /fuel-logs
Get fuel logs with optional filtering.

**Query Parameters:**
- `vehicle_id` (optional): Filter by vehicle ID
- `start_date` (optional): Filter from date (YYYY-MM-DD)
- `end_date` (optional): Filter to date (YYYY-MM-DD)

**Response:**
```json
{
  "fuel_logs": [
    {
      "id": 1,
      "vehicle_id": 1,
      "vehicle_name": "Fleet Van 001",
      "vehicle_type": "Van",
      "log_date": "2024-01-15",
      "km_driven": 145.2,
      "fuel_used": 18.5,
      "cost": 32.50,
      "efficiency": 7.85,
      "notes": "Regular maintenance route"
    }
  ],
  "count": 1
}
```

#### POST /fuel-logs
Add a new fuel log entry.

**Request Body:**
```json
{
  "vehicle_id": 1,
  "log_date": "2024-02-20",
  "km_driven": 150.5,
  "fuel_used": 19.2,
  "cost": 33.60,
  "notes": "Weekly delivery route"
}
```

#### DELETE /fuel-logs/{id}
Delete a fuel log entry.

### Statistics Endpoints

#### GET /stats
Get aggregate statistics and KPIs.

**Response:**
```json
{
  "overall_stats": {
    "total_vehicles": 6,
    "total_logs": 25,
    "total_km": 4247.8,
    "total_fuel": 428.6,
    "avg_efficiency": 9.91,
    "total_cost": 750.25
  },
  "vehicle_stats": [
    {
      "name": "Fleet Van 001",
      "type": "Van",
      "log_count": 5,
      "total_km": 744.1,
      "total_fuel": 94.7,
      "avg_efficiency": 7.86,
      "total_cost": 165.66
    }
  ]
}
```

### Machine Learning Endpoints

#### GET /predict?km={kilometers}
Predict fuel consumption using linear regression.

**Query Parameters:**
- `km` (required): Kilometers to predict fuel consumption for

**Response:**
```json
{
  "kilometers": 100,
  "predicted_fuel": 12.45,
  "model_score": 0.847,
  "training_samples": 25,
  "note": "Linear regression finds best-fit line through historical data"
}
```

#### GET /detect-anomalies
Detect fuel usage anomalies using Isolation Forest.

**Response:**
```json
{
  "anomalies": [
    {
      "id": 23,
      "vehicle_id": 1,
      "log_date": "2024-02-13",
      "km_driven": 45.2,
      "fuel_used": 25.8,
      "efficiency": 1.75,
      "anomaly_score": -0.234
    }
  ],
  "total_records_analyzed": 25,
  "anomalies_found": 3,
  "contamination_rate": 0.05,
  "note": "Isolation Forest isolates outliers (label -1) based on fuel efficiency patterns"
}
```

### Utility Endpoints

#### GET /health
Health check endpoint to verify API and database connectivity.

## 🤖 Machine Learning Features

### 1. Fuel Consumption Prediction (Linear Regression)
- **Purpose**: Predict fuel consumption based on kilometers driven
- **Algorithm**: Linear Regression from scikit-learn
- **Training Data**: Historical fuel logs with km_driven and fuel_used
- **Use Case**: Budget planning and fuel efficiency monitoring

**Implementation Notes:**
- Uses recent 1000 fuel logs for training
- Returns model score (R² coefficient) for accuracy assessment
- Simple linear relationship: `fuel_used = slope * km_driven + intercept`

### 2. Anomaly Detection (Isolation Forest)
- **Purpose**: Identify unusual fuel consumption patterns
- **Algorithm**: Isolation Forest from scikit-learn
- **Features**: kilometers driven, fuel used, efficiency (km/L)
- **Use Case**: Maintenance alerts and fraud detection

**Implementation Notes:**
- Contamination rate set to 5% (expects 5% of data to be anomalies)
- Analyzes recent 500 fuel logs
- Returns anomaly score (lower scores indicate higher anomaly probability)

## 📈 Sample Queries

### Vehicle Efficiency Analysis
```sql
SELECT v.name, SUM(f.km_driven)/SUM(f.fuel_used) AS avg_efficiency
FROM fuel_logs f
JOIN vehicles v ON f.vehicle_id = v.id
GROUP BY v.id
ORDER BY avg_efficiency DESC;
```

### Monthly Fuel Costs
```sql
SELECT DATE_FORMAT(log_date, '%Y-%m') as month,
       SUM(cost) as total_cost,
       SUM(fuel_used) as total_fuel
FROM fuel_logs
GROUP BY DATE_FORMAT(log_date, '%Y-%m')
ORDER BY month;
```

### Vehicle Performance Comparison
```sql
SELECT v.type,
       COUNT(fl.id) as total_logs,
       AVG(fl.km_driven/fl.fuel_used) as avg_efficiency,
       AVG(fl.cost) as avg_cost_per_fill
FROM vehicles v
LEFT JOIN fuel_logs fl ON v.id = fl.vehicle_id
GROUP BY v.type;
```

## 🧪 Testing the API

### Using curl

1. **Get all vehicles**:
   ```bash
   curl http://localhost:5000/vehicles
   ```

2. **Add a fuel log**:
   ```bash
   curl -X POST http://localhost:5000/fuel-logs \
     -H "Content-Type: application/json" \
     -d '{
       "vehicle_id": 1,
       "log_date": "2024-02-20",
       "km_driven": 150.5,
       "fuel_used": 19.2,
       "cost": 33.60
     }'
   ```

3. **Get fuel prediction**:
   ```bash
   curl "http://localhost:5000/predict?km=100"
   ```

4. **Detect anomalies**:
   ```bash
   curl http://localhost:5000/detect-anomalies
   ```

### Using Python requests

```python
import requests

# Get vehicles
response = requests.get('http://localhost:5000/vehicles')
vehicles = response.json()

# Add fuel log
new_log = {
    'vehicle_id': 1,
    'log_date': '2024-02-20',
    'km_driven': 150.5,
    'fuel_used': 19.2,
    'cost': 33.60
}
response = requests.post('http://localhost:5000/fuel-logs', json=new_log)

# Get prediction
response = requests.get('http://localhost:5000/predict?km=100')
prediction = response.json()
```

## 🔧 Configuration

### Database Configuration
Update the `DB_CONFIG` dictionary in both `app.py` and `init_db.py`:

```python
DB_CONFIG = {
    'host': 'localhost',        # MySQL server host
    'user': 'root',             # MySQL username
    'password': 'your_password', # MySQL password
    'database': 'fleetfuel360', # Database name
    'charset': 'utf8mb4'        # Character set
}
```

### Environment Variables (Optional)
For production deployment, consider using environment variables:

```python
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'fleetfuel360'),
    'charset': 'utf8mb4'
}
```

## 🚀 Deployment Considerations

### Production Checklist
- [ ] Use environment variables for sensitive configuration
- [ ] Enable SSL/TLS for database connections
- [ ] Implement proper logging and monitoring
- [ ] Add input validation and sanitization
- [ ] Use connection pooling for database
- [ ] Implement rate limiting
- [ ] Add API authentication and authorization
- [ ] Use WSGI server (Gunicorn, uWSGI) instead of Flask dev server

### Docker Deployment (Optional)
Create a `Dockerfile` for containerized deployment:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**:
   - Verify MySQL server is running
   - Check credentials in `DB_CONFIG`
   - Ensure MySQL user has proper permissions

2. **Import Errors**:
   - Activate virtual environment: `source venv/bin/activate`
   - Install requirements: `pip install -r requirements.txt`

3. **Port Already in Use**:
   - Change port in `app.py`: `app.run(port=5001)`
   - Or kill process using port 5000

4. **ML Model Errors**:
   - Ensure sufficient data (>10 fuel logs) for training
   - Check for zero values in fuel_used or km_driven

### Error Responses
The API returns structured error responses:

```json
{
  "error": "Vehicle not found"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation error)
- `404`: Not Found
- `500`: Internal Server Error

## 📚 Learning Resources

- **Flask Documentation**: https://flask.palletsprojects.com/
- **MySQL Documentation**: https://dev.mysql.com/doc/
- **scikit-learn Documentation**: https://scikit-learn.org/stable/
- **RESTful API Design**: https://restfulapi.net/
- **SQL Indexing Best Practices**: https://use-the-index-luke.com/

## 🤝 Contributing

This project is designed for educational purposes. Feel free to:
- Add new endpoints
- Implement additional ML models
- Improve error handling
- Add unit tests
- Enhance documentation

## 📝 License

This project is open source and available under the MIT License.

---

**Note**: This is a simplified educational project. For production use, implement proper security measures, input validation, authentication, and error handling.
