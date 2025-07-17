"""
Simple test script for FleetFuel360 API
Tests basic functionality of all endpoints
"""

import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:5000"

def test_endpoint(method, endpoint, data=None, params=None):
    """Test an API endpoint and return response"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            print(f"❌ Unsupported method: {method}")
            return None
        
        print(f"{method} {endpoint} -> {response.status_code}")
        
        if response.status_code < 400:
            return response.json()
        else:
            print(f"   Error: {response.json()}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Is the server running at {BASE_URL}?")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_api_tests():
    """Run comprehensive API tests"""
    print("FleetFuel360 API Testing")
    print("=" * 40)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    health = test_endpoint("GET", "/health")
    if health:
        print(f"   Status: {health['status']}")
        print(f"   Database: {health['database']}")
    
    # Test 2: Get all vehicles
    print("\n2. Testing get all vehicles...")
    vehicles = test_endpoint("GET", "/vehicles")
    if vehicles:
        print(f"   Found {vehicles['count']} vehicles")
        if vehicles['vehicles']:
            first_vehicle = vehicles['vehicles'][0]
            print(f"   First vehicle: {first_vehicle['name']} ({first_vehicle['type']})")
    
    # Test 3: Get vehicle by ID
    print("\n3. Testing get vehicle by ID...")
    vehicle = test_endpoint("GET", "/vehicles/1")
    if vehicle:
        print(f"   Vehicle: {vehicle['name']}")
    
    # Test 4: Add new vehicle
    print("\n4. Testing add new vehicle...")
    new_vehicle = {
        "name": "Test Vehicle",
        "type": "Car",
        "license_plate": "TEST-123",
        "year": 2023,
        "make": "Toyota",
        "model": "Test"
    }
    result = test_endpoint("POST", "/vehicles", data=new_vehicle)
    new_vehicle_id = None
    if result:
        new_vehicle_id = result['vehicle_id']
        print(f"   Created vehicle ID: {new_vehicle_id}")
    
    # Test 5: Get all fuel logs
    print("\n5. Testing get all fuel logs...")
    fuel_logs = test_endpoint("GET", "/fuel-logs")
    if fuel_logs:
        print(f"   Found {fuel_logs['count']} fuel logs")
        if fuel_logs['fuel_logs']:
            first_log = fuel_logs['fuel_logs'][0]
            print(f"   First log: {first_log['vehicle_name']} - {first_log['km_driven']}km, {first_log['fuel_used']}L")
    
    # Test 6: Add new fuel log
    print("\n6. Testing add new fuel log...")
    new_log = {
        "vehicle_id": 1,
        "log_date": datetime.now().strftime("%Y-%m-%d"),
        "km_driven": 125.5,
        "fuel_used": 15.8,
        "cost": 27.65,
        "notes": "Test log entry"
    }
    result = test_endpoint("POST", "/fuel-logs", data=new_log)
    new_log_id = None
    if result:
        new_log_id = result['log_id']
        print(f"   Created fuel log ID: {new_log_id}")
    
    # Test 7: Get fuel logs with filters
    print("\n7. Testing fuel logs with vehicle filter...")
    filtered_logs = test_endpoint("GET", "/fuel-logs", params={"vehicle_id": 1})
    if filtered_logs:
        print(f"   Found {filtered_logs['count']} logs for vehicle 1")
    
    # Test 8: Get statistics
    print("\n8. Testing statistics...")
    stats = test_endpoint("GET", "/stats")
    if stats:
        overall = stats['overall_stats']
        print(f"   Total vehicles: {overall['total_vehicles']}")
        print(f"   Total logs: {overall['total_logs']}")
        print(f"   Average efficiency: {overall['avg_efficiency']:.2f} km/L")
    
    # Test 9: Fuel prediction
    print("\n9. Testing fuel prediction...")
    prediction = test_endpoint("GET", "/predict", params={"km": 100})
    if prediction:
        print(f"   Predicted fuel for 100km: {prediction['predicted_fuel']}L")
        print(f"   Model score: {prediction['model_score']}")
    
    # Test 10: Anomaly detection
    print("\n10. Testing anomaly detection...")
    anomalies = test_endpoint("GET", "/detect-anomalies")
    if anomalies:
        print(f"   Analyzed {anomalies['total_records_analyzed']} records")
        print(f"   Found {anomalies['anomalies_found']} anomalies")
    
    # Test 11: Update vehicle (if we created one)
    if new_vehicle_id:
        print(f"\n11. Testing update vehicle {new_vehicle_id}...")
        update_data = {"name": "Updated Test Vehicle"}
        result = test_endpoint("PUT", f"/vehicles/{new_vehicle_id}", data=update_data)
        if result:
            print(f"   Updated vehicle successfully")
    
    # Cleanup: Delete test data
    if new_log_id:
        print(f"\n12. Cleaning up - deleting test fuel log {new_log_id}...")
        test_endpoint("DELETE", f"/fuel-logs/{new_log_id}")
    
    if new_vehicle_id:
        print(f"\n13. Cleaning up - deleting test vehicle {new_vehicle_id}...")
        test_endpoint("DELETE", f"/vehicles/{new_vehicle_id}")
    
    print("\n" + "=" * 40)
    print("API testing completed!")
    print("✅ If you see mostly 200 status codes, the API is working correctly.")
    print("❌ If you see 500 errors, check the database connection and setup.")

def test_error_handling():
    """Test error handling scenarios"""
    print("\nTesting Error Handling")
    print("=" * 30)
    
    # Test invalid vehicle ID
    print("1. Testing invalid vehicle ID...")
    test_endpoint("GET", "/vehicles/999")
    
    # Test invalid data
    print("2. Testing invalid fuel log data...")
    invalid_log = {"vehicle_id": 999, "log_date": "invalid-date"}
    test_endpoint("POST", "/fuel-logs", data=invalid_log)
    
    # Test missing required fields
    print("3. Testing missing required fields...")
    incomplete_vehicle = {"name": "Test"}  # missing 'type'
    test_endpoint("POST", "/vehicles", data=incomplete_vehicle)
    
    # Test invalid prediction parameter
    print("4. Testing invalid prediction parameter...")
    test_endpoint("GET", "/predict", params={"km": -10})

if __name__ == "__main__":
    print("Starting FleetFuel360 API Tests...")
    print("Make sure the server is running: python app.py")
    print()
    
    input("Press Enter to start tests...")
    
    run_api_tests()
    
    print("\n" + "=" * 50)
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("TESTING COMPLETE")
    print("=" * 50)
    print("Next steps:")
    print("1. Check that all endpoints returned 200 status codes")
    print("2. Review any error messages above")
    print("3. Test individual endpoints with curl or Postman")
    print("4. Check the database to verify data was created/updated correctly")
