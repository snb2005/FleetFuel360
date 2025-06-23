# FleetFuel360 🚛⛽

**A logistics analytics platform for fuel monitoring and anomaly detection.**

## 🔗 Tech Stack

* Python 3.10+
* Flask 2.3+
* PostgreSQL 13+
* Scikit-learn (ML)
* Bootstrap + Chart.js (Frontend)

## 🚀 Key Features

* Real-time fuel efficiency dashboard
* ML-powered anomaly detection using Isolation Forest
* Fleet-wide KPIs and performance comparison
* Admin dashboard and vehicle management

## 🔧 Quick Setup

### 1. Clone Repository

```bash
git clone https://github.com/snb2005/FleetFuel360.git
cd FleetFuel360
```

### 2. Setup Environment

```bash
python -m venv venv
source venv/bin/activate  # For Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Database

```sql
CREATE DATABASE fleetfuel360;
CREATE USER fleetfuel_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE fleetfuel360 TO fleetfuel_user;
```

### 4. Initialize Database

```bash
python backend/db/init_db.py
```

### 5. Start App

```bash
python app.py
```

Visit: [http://localhost:5000](http://localhost:5000)

## 📊 API Endpoints

| Endpoint                | Method | Description            |
| ----------------------- | ------ | ---------------------- |
| `/api/vehicles`         | GET    | List all vehicles      |
| `/api/fuel-logs`        | GET    | Fuel data for vehicles |
| `/api/anomalies`        | GET    | Detected anomalies     |
| `/api/detect-anomalies` | POST   | Run ML detection       |

## 🤖 ML Model

* Algorithm: Isolation Forest
* Features: `fuel_efficiency`, `fuel_used`, `km_driven`, `timestamp`
* Anomaly Rate: 5%

## 📈 Jupyter EDA

```bash
jupyter notebook notebooks/eda.ipynb
```

* Fuel trends, performance comparison, and anomaly visualization

## 🚧 Deployment

* Ready for Render.com deployment (with `render.yaml`)
* Docker support available

## 🔐 Security

* Basic Auth support
* CSRF & XSS protection
* HTTPS (in production)

---

**FleetFuel360** - *Optimizing logistics with smart fuel analytics*
