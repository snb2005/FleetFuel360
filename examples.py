"""
FleetFuel360 API Usage Examples
Demonstrates how to interact with the API programmatically
"""

import requests
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np

BASE_URL = "http://localhost:5000"

class FleetFuelAPI:
    """Python client for FleetFuel360 API"""
    
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
    
    def get_vehicles(self, vehicle_type=None):
        """Get all vehicles, optionally filtered by type"""
        params = {"type": vehicle_type} if vehicle_type else None
        response = requests.get(f"{self.base_url}/vehicles", params=params)
        return response.json() if response.status_code == 200 else None
    
    def add_vehicle(self, name, vehicle_type, license_plate="", year=None, make="", model=""):
        """Add a new vehicle"""
        data = {
            "name": name,
            "type": vehicle_type,
            "license_plate": license_plate,
            "year": year,
            "make": make,
            "model": model
        }
        response = requests.post(f"{self.base_url}/vehicles", json=data)
        return response.json() if response.status_code == 201 else None
    
    def get_fuel_logs(self, vehicle_id=None, start_date=None, end_date=None):
        """Get fuel logs with optional filtering"""
        params = {}
        if vehicle_id:
            params["vehicle_id"] = vehicle_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response = requests.get(f"{self.base_url}/fuel-logs", params=params)
        return response.json() if response.status_code == 200 else None
    
    def add_fuel_log(self, vehicle_id, log_date, km_driven, fuel_used, cost=None, notes=""):
        """Add a new fuel log"""
        data = {
            "vehicle_id": vehicle_id,
            "log_date": log_date,
            "km_driven": km_driven,
            "fuel_used": fuel_used,
            "cost": cost,
            "notes": notes
        }
        response = requests.post(f"{self.base_url}/fuel-logs", json=data)
        return response.json() if response.status_code == 201 else None
    
    def get_stats(self):
        """Get fleet statistics"""
        response = requests.get(f"{self.base_url}/stats")
        return response.json() if response.status_code == 200 else None
    
    def predict_fuel(self, kilometers):
        """Predict fuel consumption for given kilometers"""
        response = requests.get(f"{self.base_url}/predict", params={"km": kilometers})
        return response.json() if response.status_code == 200 else None
    
    def detect_anomalies(self):
        """Detect anomalies in fuel usage"""
        response = requests.get(f"{self.base_url}/detect-anomalies")
        return response.json() if response.status_code == 200 else None

def example_basic_usage():
    """Example 1: Basic API usage"""
    print("Example 1: Basic API Usage")
    print("=" * 40)
    
    api = FleetFuelAPI()
    
    # Get all vehicles
    vehicles = api.get_vehicles()
    if vehicles:
        print(f"Total vehicles: {vehicles['count']}")
        for vehicle in vehicles['vehicles'][:3]:  # Show first 3
            print(f"  - {vehicle['name']} ({vehicle['type']})")
    
    # Get fuel logs for first vehicle
    if vehicles and vehicles['vehicles']:
        vehicle_id = vehicles['vehicles'][0]['id']
        logs = api.get_fuel_logs(vehicle_id=vehicle_id)
        if logs:
            print(f"\nFuel logs for vehicle {vehicle_id}: {logs['count']} records")
            for log in logs['fuel_logs'][:3]:  # Show first 3
                print(f"  - {log['log_date']}: {log['km_driven']}km, {log['fuel_used']}L (eff: {log['efficiency']})")
    
    # Get overall statistics
    stats = api.get_stats()
    if stats:
        overall = stats['overall_stats']
        print(f"\nFleet Statistics:")
        print(f"  Total vehicles: {overall['total_vehicles']}")
        print(f"  Total logs: {overall['total_logs']}")
        print(f"  Total kilometers: {overall['total_km']}")
        print(f"  Average efficiency: {overall['avg_efficiency']:.2f} km/L")

def example_ml_features():
    """Example 2: Machine Learning features"""
    print("\nExample 2: Machine Learning Features")
    print("=" * 40)
    
    api = FleetFuelAPI()
    
    # Test fuel prediction for different distances
    distances = [50, 100, 150, 200, 250]
    predictions = []
    
    print("Fuel Consumption Predictions:")
    for km in distances:
        prediction = api.predict_fuel(km)
        if prediction:
            predictions.append((km, prediction['predicted_fuel']))
            print(f"  {km} km -> {prediction['predicted_fuel']:.2f} L")
    
    # Detect anomalies
    anomalies = api.detect_anomalies()
    if anomalies:
        print(f"\nAnomaly Detection Results:")
        print(f"  Records analyzed: {anomalies['total_records_analyzed']}")
        print(f"  Anomalies found: {anomalies['anomalies_found']}")
        
        if anomalies['anomalies']:
            print("  Anomalous entries:")
            for anomaly in anomalies['anomalies'][:3]:  # Show first 3
                print(f"    - {anomaly['log_date']}: {anomaly['km_driven']}km, {anomaly['fuel_used']}L")
                print(f"      Efficiency: {anomaly['efficiency']:.2f} km/L")

def example_data_analysis():
    """Example 3: Data analysis and visualization"""
    print("\nExample 3: Data Analysis")
    print("=" * 40)
    
    api = FleetFuelAPI()
    
    # Get all fuel logs
    logs = api.get_fuel_logs()
    if not logs or not logs['fuel_logs']:
        print("No fuel logs found for analysis")
        return
    
    # Analyze efficiency by vehicle type
    vehicle_types = {}
    for log in logs['fuel_logs']:
        vehicle_type = log['vehicle_type']
        if vehicle_type not in vehicle_types:
            vehicle_types[vehicle_type] = []
        vehicle_types[vehicle_type].append(log['efficiency'])
    
    print("Efficiency by Vehicle Type:")
    for vehicle_type, efficiencies in vehicle_types.items():
        # Filter out None values
        valid_efficiencies = [e for e in efficiencies if e is not None]
        if valid_efficiencies:
            avg_efficiency = sum(valid_efficiencies) / len(valid_efficiencies)
            print(f"  {vehicle_type}: {avg_efficiency:.2f} km/L (avg)")
    
    # Find most and least efficient vehicles
    vehicle_stats = {}
    for log in logs['fuel_logs']:
        vehicle_name = log['vehicle_name']
        if vehicle_name not in vehicle_stats:
            vehicle_stats[vehicle_name] = []
        if log['efficiency']:
            vehicle_stats[vehicle_name].append(log['efficiency'])
    
    print("\nVehicle Efficiency Rankings:")
    vehicle_averages = []
    for vehicle, efficiencies in vehicle_stats.items():
        if efficiencies:
            avg_eff = sum(efficiencies) / len(efficiencies)
            vehicle_averages.append((vehicle, avg_eff))
    
    # Sort by efficiency
    vehicle_averages.sort(key=lambda x: x[1], reverse=True)
    
    print("Most efficient vehicles:")
    for vehicle, efficiency in vehicle_averages[:3]:
        print(f"  {vehicle}: {efficiency:.2f} km/L")
    
    print("Least efficient vehicles:")
    for vehicle, efficiency in vehicle_averages[-3:]:
        print(f"  {vehicle}: {efficiency:.2f} km/L")

def example_fleet_management():
    """Example 4: Fleet management workflow"""
    print("\nExample 4: Fleet Management Workflow")
    print("=" * 40)
    
    api = FleetFuelAPI()
    
    # Scenario: Add a new vehicle and log some fuel entries
    print("Adding a new vehicle...")
    new_vehicle = api.add_vehicle(
        name="Demo Vehicle",
        vehicle_type="Car",
        license_plate="DEMO-123",
        year=2023,
        make="Toyota",
        model="Camry"
    )
    
    if new_vehicle:
        vehicle_id = new_vehicle['vehicle_id']
        print(f"Created vehicle ID: {vehicle_id}")
        
        # Add some fuel logs for the new vehicle
        print("Adding fuel logs...")
        today = datetime.now()
        
        # Simulate a week of driving
        for i in range(7):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            km_driven = 45 + (i * 10)  # Varying distances
            fuel_used = 4.5 + (i * 0.8)  # Varying fuel consumption
            cost = fuel_used * 1.75  # Assume $1.75 per liter
            
            log_result = api.add_fuel_log(
                vehicle_id=vehicle_id,
                log_date=date,
                km_driven=km_driven,
                fuel_used=fuel_used,
                cost=cost,
                notes=f"Day {i+1} driving"
            )
            
            if log_result:
                print(f"  Added log: {date} - {km_driven}km, {fuel_used:.1f}L")
        
        # Get stats for the new vehicle
        vehicle_logs = api.get_fuel_logs(vehicle_id=vehicle_id)
        if vehicle_logs:
            total_km = sum(log['km_driven'] for log in vehicle_logs['fuel_logs'])
            total_fuel = sum(log['fuel_used'] for log in vehicle_logs['fuel_logs'])
            avg_efficiency = total_km / total_fuel if total_fuel > 0 else 0
            
            print(f"\nNew vehicle summary:")
            print(f"  Total logs: {vehicle_logs['count']}")
            print(f"  Total kilometers: {total_km:.1f} km")
            print(f"  Total fuel: {total_fuel:.1f} L")
            print(f"  Average efficiency: {avg_efficiency:.2f} km/L")
        
        # Clean up - delete the demo vehicle
        print(f"\nCleaning up demo vehicle...")
        delete_response = requests.delete(f"{BASE_URL}/vehicles/{vehicle_id}")
        if delete_response.status_code == 200:
            print("Demo vehicle deleted successfully")

def main():
    """Main function to run all examples"""
    print("FleetFuel360 API Examples")
    print("=" * 50)
    print("Make sure the API server is running: python app.py")
    print()
    
    try:
        # Test connection
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ API server not responding. Please start the server first.")
            return
        
        print("✅ API server is running\n")
        
        # Run examples
        example_basic_usage()
        example_ml_features()
        example_data_analysis()
        example_fleet_management()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server.")
        print("Please ensure the server is running: python app.py")
    except Exception as e:
        print(f"❌ Error running examples: {e}")

if __name__ == "__main__":
    main()
