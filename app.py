"""
FleetFuel360 - Simplified Fuel Analytics Backend
A Flask-based API for vehicle fleet management and fuel analytics with basic ML integration.
"""

from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime
import logging
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
import numpy as np
import pandas as pd

app = Flask(__name__)

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',  # Change this to your MySQL password
    'database': 'fleetfuel360',
    'charset': 'utf8mb4'
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Create and return a MySQL database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def execute_query(query, params=None, fetch_all=False, fetch_one=False):
    """Execute a SQL query and return results"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch_all:
            result = cursor.fetchall()
        elif fetch_one:
            result = cursor.fetchone()
        else:
            connection.commit()
            result = cursor.lastrowid
        
        cursor.close()
        connection.close()
        return result
    except Error as e:
        logger.error(f"Query execution error: {e}")
        return None

# ===================
# VEHICLE ENDPOINTS
# ===================

@app.route('/vehicles', methods=['GET'])
def get_vehicles():
    """Get all vehicles with optional filtering"""
    vehicle_type = request.args.get('type')
    
    # Build query with optional type filter
    query = "SELECT * FROM vehicles"
    params = None
    
    if vehicle_type:
        query += " WHERE type = %s"
        params = (vehicle_type,)
    
    query += " ORDER BY name"
    
    vehicles = execute_query(query, params, fetch_all=True)
    
    if vehicles is None:
        return jsonify({"error": "Database error"}), 500
    
    return jsonify({
        "vehicles": vehicles,
        "count": len(vehicles)
    })

@app.route('/vehicles', methods=['POST'])
def add_vehicle():
    """Add a new vehicle"""
    data = request.get_json()
    
    # Validate required fields
    if not data or 'name' not in data or 'type' not in data:
        return jsonify({"error": "Missing required fields: name, type"}), 400
    
    # Insert new vehicle
    query = """
    INSERT INTO vehicles (name, type, license_plate, year, make, model)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    params = (
        data['name'],
        data['type'],
        data.get('license_plate', ''),
        data.get('year'),
        data.get('make', ''),
        data.get('model', '')
    )
    
    vehicle_id = execute_query(query, params)
    
    if vehicle_id is None:
        return jsonify({"error": "Failed to add vehicle"}), 500
    
    return jsonify({
        "message": "Vehicle added successfully",
        "vehicle_id": vehicle_id
    }), 201

@app.route('/vehicles/<int:vehicle_id>', methods=['GET'])
def get_vehicle(vehicle_id):
    """Get a specific vehicle by ID"""
    query = "SELECT * FROM vehicles WHERE id = %s"
    vehicle = execute_query(query, (vehicle_id,), fetch_one=True)
    
    if not vehicle:
        return jsonify({"error": "Vehicle not found"}), 404
    
    return jsonify(vehicle)

@app.route('/vehicles/<int:vehicle_id>', methods=['PUT'])
def update_vehicle(vehicle_id):
    """Update a vehicle"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Build dynamic update query
    fields = []
    values = []
    
    for field in ['name', 'type', 'license_plate', 'year', 'make', 'model']:
        if field in data:
            fields.append(f"{field} = %s")
            values.append(data[field])
    
    if not fields:
        return jsonify({"error": "No valid fields to update"}), 400
    
    values.append(vehicle_id)
    query = f"UPDATE vehicles SET {', '.join(fields)} WHERE id = %s"
    
    result = execute_query(query, values)
    
    if result is None:
        return jsonify({"error": "Failed to update vehicle"}), 500
    
    return jsonify({"message": "Vehicle updated successfully"})

@app.route('/vehicles/<int:vehicle_id>', methods=['DELETE'])
def delete_vehicle(vehicle_id):
    """Delete a vehicle"""
    # First check if vehicle exists
    vehicle = execute_query("SELECT id FROM vehicles WHERE id = %s", (vehicle_id,), fetch_one=True)
    
    if not vehicle:
        return jsonify({"error": "Vehicle not found"}), 404
    
    # Delete the vehicle (fuel_logs will be handled by CASCADE)
    result = execute_query("DELETE FROM vehicles WHERE id = %s", (vehicle_id,))
    
    if result is None:
        return jsonify({"error": "Failed to delete vehicle"}), 500
    
    return jsonify({"message": "Vehicle deleted successfully"})

# ===================
# FUEL LOG ENDPOINTS
# ===================

@app.route('/fuel-logs', methods=['GET'])
def get_fuel_logs():
    """Get fuel logs with optional filtering"""
    vehicle_id = request.args.get('vehicle_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build query with optional filters
    query = """
    SELECT fl.*, v.name as vehicle_name, v.type as vehicle_type
    FROM fuel_logs fl
    JOIN vehicles v ON fl.vehicle_id = v.id
    WHERE 1=1
    """
    
    params = []
    
    if vehicle_id:
        query += " AND fl.vehicle_id = %s"
        params.append(vehicle_id)
    
    if start_date:
        query += " AND fl.log_date >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND fl.log_date <= %s"
        params.append(end_date)
    
    query += " ORDER BY fl.log_date DESC"
    
    logs = execute_query(query, params, fetch_all=True)
    
    if logs is None:
        return jsonify({"error": "Database error"}), 500
    
    # Calculate efficiency for each log
    for log in logs:
        if log['fuel_used'] and log['fuel_used'] > 0:
            log['efficiency'] = round(log['km_driven'] / log['fuel_used'], 2)
        else:
            log['efficiency'] = None
    
    return jsonify({
        "fuel_logs": logs,
        "count": len(logs)
    })

@app.route('/fuel-logs', methods=['POST'])
def add_fuel_log():
    """Add a new fuel log entry"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['vehicle_id', 'log_date', 'km_driven', 'fuel_used']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {', '.join(required_fields)}"}), 400
    
    # Validate that vehicle exists
    vehicle = execute_query("SELECT id FROM vehicles WHERE id = %s", (data['vehicle_id'],), fetch_one=True)
    if not vehicle:
        return jsonify({"error": "Vehicle not found"}), 400
    
    # Insert new fuel log
    query = """
    INSERT INTO fuel_logs (vehicle_id, log_date, km_driven, fuel_used, cost, notes)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    params = (
        data['vehicle_id'],
        data['log_date'],
        data['km_driven'],
        data['fuel_used'],
        data.get('cost'),
        data.get('notes', '')
    )
    
    log_id = execute_query(query, params)
    
    if log_id is None:
        return jsonify({"error": "Failed to add fuel log"}), 500
    
    return jsonify({
        "message": "Fuel log added successfully",
        "log_id": log_id
    }), 201

@app.route('/fuel-logs/<int:log_id>', methods=['DELETE'])
def delete_fuel_log(log_id):
    """Delete a fuel log entry"""
    # First check if log exists
    log = execute_query("SELECT id FROM fuel_logs WHERE id = %s", (log_id,), fetch_one=True)
    
    if not log:
        return jsonify({"error": "Fuel log not found"}), 404
    
    # Delete the log
    result = execute_query("DELETE FROM fuel_logs WHERE id = %s", (log_id,))
    
    if result is None:
        return jsonify({"error": "Failed to delete fuel log"}), 500
    
    return jsonify({"message": "Fuel log deleted successfully"})

# ===================
# STATISTICS ENDPOINTS
# ===================

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get aggregate statistics and KPIs"""
    # Get overall statistics
    stats_query = """
    SELECT 
        COUNT(DISTINCT v.id) as total_vehicles,
        COUNT(fl.id) as total_logs,
        SUM(fl.km_driven) as total_km,
        SUM(fl.fuel_used) as total_fuel,
        AVG(fl.km_driven / fl.fuel_used) as avg_efficiency,
        SUM(fl.cost) as total_cost
    FROM vehicles v
    LEFT JOIN fuel_logs fl ON v.id = fl.vehicle_id
    """
    
    stats = execute_query(stats_query, fetch_one=True)
    
    # Get per-vehicle statistics
    vehicle_stats_query = """
    SELECT 
        v.name,
        v.type,
        COUNT(fl.id) as log_count,
        SUM(fl.km_driven) as total_km,
        SUM(fl.fuel_used) as total_fuel,
        AVG(fl.km_driven / fl.fuel_used) as avg_efficiency,
        SUM(fl.cost) as total_cost
    FROM vehicles v
    LEFT JOIN fuel_logs fl ON v.id = fl.vehicle_id
    GROUP BY v.id, v.name, v.type
    ORDER BY total_km DESC
    """
    
    vehicle_stats = execute_query(vehicle_stats_query, fetch_all=True)
    
    if stats is None or vehicle_stats is None:
        return jsonify({"error": "Database error"}), 500
    
    # Format numbers
    for stat in vehicle_stats:
        if stat['avg_efficiency']:
            stat['avg_efficiency'] = round(stat['avg_efficiency'], 2)
        if stat['total_cost']:
            stat['total_cost'] = round(stat['total_cost'], 2)
    
    return jsonify({
        "overall_stats": stats,
        "vehicle_stats": vehicle_stats
    })

# ===================
# MACHINE LEARNING ENDPOINTS
# ===================

@app.route('/predict', methods=['GET'])
def predict_fuel():
    """Predict fuel consumption based on kilometers using linear regression"""
    km = request.args.get('km', type=float)
    
    if km is None or km <= 0:
        return jsonify({"error": "Valid 'km' parameter required"}), 400
    
    # Get training data from database
    query = """
    SELECT km_driven, fuel_used
    FROM fuel_logs
    WHERE km_driven > 0 AND fuel_used > 0
    ORDER BY log_date DESC
    LIMIT 1000
    """
    
    data = execute_query(query, fetch_all=True)
    
    if not data or len(data) < 2:
        return jsonify({"error": "Insufficient data for prediction"}), 400
    
    # Prepare data for ML model
    X = np.array([[row['km_driven']] for row in data])
    y = np.array([row['fuel_used'] for row in data])
    
    # Train linear regression model
    model = LinearRegression()
    model.fit(X, y)
    
    # Make prediction
    predicted_fuel = model.predict([[km]])[0]
    
    # Calculate model metrics
    train_score = model.score(X, y)
    
    return jsonify({
        "kilometers": km,
        "predicted_fuel": round(predicted_fuel, 2),
        "model_score": round(train_score, 3),
        "training_samples": len(data),
        "note": "Linear regression finds best-fit line through historical data"
    })

@app.route('/detect-anomalies', methods=['GET'])
def detect_anomalies():
    """Detect anomalies in fuel usage using Isolation Forest"""
    # Get recent fuel logs for anomaly detection
    query = """
    SELECT id, vehicle_id, log_date, km_driven, fuel_used,
           (km_driven / fuel_used) as efficiency
    FROM fuel_logs
    WHERE km_driven > 0 AND fuel_used > 0
    ORDER BY log_date DESC
    LIMIT 500
    """
    
    data = execute_query(query, fetch_all=True)
    
    if not data or len(data) < 10:
        return jsonify({"error": "Insufficient data for anomaly detection"}), 400
    
    # Prepare features for anomaly detection
    features = []
    for row in data:
        features.append([
            row['km_driven'],
            row['fuel_used'],
            row['efficiency']
        ])
    
    X = np.array(features)
    
    # Train Isolation Forest model
    # contamination=0.05 means expect 5% of data to be anomalies
    model = IsolationForest(contamination=0.05, random_state=42)
    predictions = model.fit_predict(X)
    
    # Find anomalies (prediction = -1 means anomaly)
    anomalies = []
    for i, pred in enumerate(predictions):
        if pred == -1:
            anomaly_data = data[i].copy()
            anomaly_data['anomaly_score'] = model.score_samples([features[i]])[0]
            anomalies.append(anomaly_data)
    
    return jsonify({
        "anomalies": anomalies,
        "total_records_analyzed": len(data),
        "anomalies_found": len(anomalies),
        "contamination_rate": 0.05,
        "note": "Isolation Forest isolates outliers (label -1) based on fuel efficiency patterns"
    })

# ===================
# ERROR HANDLERS
# ===================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# ===================
# HEALTH CHECK
# ===================

@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    try:
        # Test database connection
        connection = get_db_connection()
        if connection:
            connection.close()
            db_status = "connected"
        else:
            db_status = "disconnected"
        
        return jsonify({
            "status": "healthy",
            "database": db_status,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/')
def index():
    """Serve the main index page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Serve the main dashboard page"""
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
