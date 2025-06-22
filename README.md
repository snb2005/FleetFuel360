# FleetFuel360 🚛⛽

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Production-grade logistics analytics platform for fuel efficiency monitoring and anomaly detection.**

FleetFuel360 is a comprehensive dashboard system that helps logistics companies optimize fuel consumption, detect inefficiencies, and reduce operational costs through advanced analytics and machine learning.

## 🎯 Features

### 📊 **Analytics Dashboard**
- Real-time fuel efficiency monitoring
- Interactive charts with Chart.js
- Vehicle performance comparison
- Fleet-wide statistics and KPIs

### 🤖 **ML-Powered Anomaly Detection**
- Isolation Forest algorithm for anomaly detection
- Automated flagging of unusual fuel consumption patterns
- Configurable sensitivity thresholds
- Real-time anomaly scoring

### 🚛 **Fleet Management**
- Multi-vehicle tracking and analysis
- Per-vehicle and per-route efficiency metrics
- Historical trend analysis
- Performance benchmarking

### 📈 **Business Intelligence**
- Actionable recommendations engine
- Cost savings identification
- Maintenance scheduling insights
- Driver performance analytics

## 🏗️ Architecture

```
FleetFuel360/
├── 🖥️  Backend (Flask + PostgreSQL)
│   ├── REST API endpoints
│   ├── SQLAlchemy ORM models
│   ├── Business logic services
│   └── Database management
├── 🤖 ML Engine (Scikit-learn)
│   ├── Isolation Forest anomaly detection
│   ├── Data preprocessing pipeline
│   └── Feature engineering
├── 🌐 Frontend (Bootstrap + Chart.js)
│   ├── Responsive dashboard UI
│   ├── Interactive visualizations
│   └── Real-time data updates
└── 📊 Analytics (Jupyter Notebooks)
    ├── Exploratory data analysis
    ├── Statistical insights
    └── Performance reporting
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **PostgreSQL 13+**
- **Git**

### 1. Clone & Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd FleetFuel360

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Start PostgreSQL service
sudo systemctl start postgresql  # Linux
# brew services start postgresql  # macOS

# Create database and user
sudo -u postgres psql
```

```sql
-- In PostgreSQL console
CREATE DATABASE fleetfuel360;
CREATE USER fleetfuel_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE fleetfuel360 TO fleetfuel_user;
\q
```

### 3. Configure Environment

```bash
# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=fleetfuel360
export POSTGRES_USER=fleetfuel_user
export POSTGRES_PASSWORD=your_secure_password
export FLASK_ENV=development
```

### 4. Initialize Database

```bash
# Run database initialization
python backend/db/init_db.py
```

Expected output:
```
🚀 Initializing FleetFuel360 Database...
✅ Created database: fleetfuel360
✅ Schema executed successfully
✅ CSV data loaded successfully
✅ Vehicles in database: 5
✅ Fuel logs in database: 56
🎉 Database initialization completed successfully!
```

### 5. Launch Application

```bash
# Start the Flask application
python app.py
```

Visit: **http://localhost:5000**

## 📊 Using the Dashboard

### Main Dashboard
- **Fleet Overview**: Key performance indicators
- **Efficiency Timeline**: Fuel efficiency trends over time
- **Vehicle Comparison**: Performance benchmarking
- **Anomaly Detection**: Real-time alerts and flagged records

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Service health check |
| `/api/vehicles` | GET | List all vehicles |
| `/api/fuel-logs` | GET | Get fuel consumption data |
| `/api/anomalies` | GET | Get detected anomalies |
| `/api/analysis` | GET | Get comprehensive analysis |
| `/api/detect-anomalies` | POST | Run anomaly detection |
| `/api/statistics` | GET | Get fleet statistics |
| `/api/chart-data` | GET | Get Chart.js formatted data |

### Query Parameters

```bash
# Filter by vehicle
curl "http://localhost:5000/api/fuel-logs?vehicle_id=TRUCK001"

# Set time range
curl "http://localhost:5000/api/statistics?days_back=30"

# Get chart data
curl "http://localhost:5000/api/chart-data?type=efficiency_timeline&days_back=7"
```

## 🤖 Machine Learning

### Anomaly Detection Model

The system uses **Isolation Forest** algorithm to detect fuel efficiency anomalies:

```python
# Model configuration
contamination = 0.05  # Expected 5% anomaly rate
features = [
    'fuel_efficiency',
    'fuel_used', 
    'km_driven',
    'time_features',
    'vehicle_statistics'
]
```

### Training the Model

```bash
# Manual model training
python -c "
from backend.services.analyze_fuel import FuelAnalysisService
from backend.db.init_db import get_db_session

service = FuelAnalysisService(get_db_session())
service.train_new_model()
"
```

### Anomaly Types Detected

1. **Fuel Efficiency Outliers**: Unusually high/low km/L ratios
2. **Consumption Spikes**: Unexpected fuel usage patterns  
3. **Distance-Fuel Mismatches**: Inconsistent distance vs fuel relationships
4. **Temporal Anomalies**: Unusual patterns by time/day
5. **Vehicle-Specific Deviations**: Performance outside normal ranges

## 📈 Data Analysis

### Jupyter Notebook EDA

```bash
# Launch Jupyter
jupyter notebook notebooks/eda.ipynb
```

The notebook includes:
- **Statistical Analysis**: Descriptive statistics and distributions
- **Correlation Analysis**: Relationships between variables
- **Trend Analysis**: Time-based patterns and seasonality
- **Vehicle Comparison**: Performance benchmarking
- **Anomaly Visualization**: Outlier detection and analysis

### Key Metrics

- **Fleet Efficiency**: Average km/L across all vehicles
- **Anomaly Rate**: Percentage of flagged records
- **Vehicle Performance**: Individual vehicle benchmarks
- **Trend Analysis**: Efficiency improvements/degradation
- **Cost Impact**: Fuel savings opportunities

## 🔧 Configuration

### Database Settings (`backend/config.py`)

```python
class Config:
    POSTGRES_HOST = 'localhost'
    POSTGRES_PORT = '5432' 
    POSTGRES_DB = 'fleetfuel360'
    POSTGRES_USER = 'fleetfuel_user'
    POSTGRES_PASSWORD = 'your_password'
    
    # ML Settings
    ANOMALY_THRESHOLD = 0.1
    ISOLATION_FOREST_CONTAMINATION = 0.05
```

### ML Model Parameters

```python
# Isolation Forest Configuration
model = IsolationForest(
    contamination=0.05,      # 5% expected anomaly rate
    n_estimators=100,        # Number of trees
    max_samples='auto',      # Samples per tree
    random_state=42          # Reproducibility
)
```

## 📊 Sample Data Format

### Fuel Logs CSV Structure

```csv
vehicle_id,timestamp,km_driven,fuel_used
TRUCK001,2025-06-01 08:00:00,120.5,15.2
TRUCK001,2025-06-01 14:30:00,85.3,10.8
TRUCK002,2025-06-01 09:00:00,105.8,14.2
```

### API Response Format

```json
{
  "status": "success",
  "count": 56,
  "fuel_logs": [
    {
      "id": 1,
      "vehicle_id": "TRUCK001",
      "timestamp": "2025-06-01T08:00:00",
      "km_driven": 120.5,
      "fuel_used": 15.2,
      "fuel_efficiency": 7.93,
      "is_anomaly": false,
      "anomaly_score": -0.05
    }
  ]
}
```

## 🧪 Testing

### Run Tests

```bash
# Install testing dependencies
pip install pytest pytest-flask

# Run test suite
pytest tests/

# Run specific test
pytest tests/test_api.py::test_fuel_logs_endpoint
```

### API Testing

```bash
# Test health endpoint
curl -X GET http://localhost:5000/api/health

# Test anomaly detection
curl -X POST http://localhost:5000/api/detect-anomalies \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id": "TRUCK001", "update_db": true}'
```

## 🚀 Deployment

### Production Setup

1. **Environment Configuration**
```bash
export FLASK_ENV=production
export SECRET_KEY="your-production-secret-key"
export POSTGRES_HOST="your-prod-db-host"
```

2. **Database Migration**
```bash
# Backup existing data
pg_dump fleetfuel360 > backup.sql

# Run schema updates
python backend/db/init_db.py
```

3. **Process Management**
```bash
# Using Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Using systemd service
sudo systemctl enable fleetfuel360
sudo systemctl start fleetfuel360
```

### Docker Deployment

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

```bash
# Build and run
docker build -t fleetfuel360 .
docker run -p 5000:5000 fleetfuel360
```

## 📈 Performance Optimization

### Database Optimization

- **Indexing**: Key indexes on `vehicle_id`, `timestamp`, `is_anomaly`
- **Partitioning**: Consider date-based partitioning for large datasets
- **Connection Pooling**: Use SQLAlchemy connection pooling

### Caching Strategy

```python
# Redis caching for frequent queries
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@cache.memoize(timeout=300)
def get_fleet_statistics():
    # Cached for 5 minutes
    return calculate_statistics()
```

## 🔒 Security

### Authentication & Authorization

```python
# Basic authentication setup
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    # Implement your authentication logic
    return check_user_credentials(username, password)
```

### Data Protection

- **SQL Injection**: SQLAlchemy ORM prevents SQL injection
- **XSS Protection**: Input sanitization and validation
- **CSRF Protection**: CSRF tokens for form submissions
- **HTTPS**: SSL/TLS encryption for production

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U fleetfuel_user -d fleetfuel360
```

**Model Training Issues**
```bash
# Check data availability
python -c "
from backend.db.init_db import get_db_session
from backend.models.fuel_log import FuelLog
session = get_db_session()
print(f'Records: {len(FuelLog.get_all(session))}')
"
```

**Port Already in Use**
```bash
# Find process using port 5000
lsof -i :5000
kill -9 <PID>
```

### Debug Mode

```bash
# Enable detailed logging
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include unit tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **Scikit-learn** - Machine learning library
- **Chart.js** - Frontend visualization
- **Bootstrap** - UI framework
- **PostgreSQL** - Database system

## 📞 Support

For support and questions:

- 📧 **Email**: support@fleetfuel360.com
- 📖 **Documentation**: [Link to detailed docs]
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**FleetFuel360** - *Optimizing logistics through intelligent fuel analytics* 🚛⛽📊
