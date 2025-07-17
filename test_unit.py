"""
Unit tests for FleetFuel360 API
Simple test cases to verify basic functionality
"""

import unittest
import json
from datetime import datetime
import sys
import os

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, execute_query

class FleetFuel360TestCase(unittest.TestCase):
    """Test cases for FleetFuel360 API"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.app = app.test_client()
        self.app.testing = True
    
    def tearDown(self):
        """Clean up after each test method"""
        pass
    
    def test_health_check(self):
        """Test the health check endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('database', data)
        self.assertIn('timestamp', data)
    
    def test_get_vehicles(self):
        """Test getting all vehicles"""
        response = self.app.get('/vehicles')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('vehicles', data)
        self.assertIn('count', data)
        self.assertIsInstance(data['vehicles'], list)
        self.assertIsInstance(data['count'], int)
    
    def test_get_vehicles_with_type_filter(self):
        """Test getting vehicles filtered by type"""
        response = self.app.get('/vehicles?type=Van')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('vehicles', data)
        
        # Check that all returned vehicles are vans
        for vehicle in data['vehicles']:
            self.assertEqual(vehicle['type'], 'Van')
    
    def test_get_vehicle_by_id(self):
        """Test getting a specific vehicle by ID"""
        # First get all vehicles to get a valid ID
        response = self.app.get('/vehicles')
        data = json.loads(response.data)
        
        if data['vehicles']:
            vehicle_id = data['vehicles'][0]['id']
            
            # Test getting specific vehicle
            response = self.app.get(f'/vehicles/{vehicle_id}')
            self.assertEqual(response.status_code, 200)
            
            vehicle_data = json.loads(response.data)
            self.assertEqual(vehicle_data['id'], vehicle_id)
            self.assertIn('name', vehicle_data)
            self.assertIn('type', vehicle_data)
    
    def test_get_nonexistent_vehicle(self):
        """Test getting a vehicle that doesn't exist"""
        response = self.app.get('/vehicles/999999')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_add_vehicle(self):
        """Test adding a new vehicle"""
        new_vehicle = {
            'name': 'Test Vehicle',
            'type': 'Car',
            'license_plate': 'TEST-123',
            'year': 2023,
            'make': 'Toyota',
            'model': 'Test'
        }
        
        response = self.app.post('/vehicles', 
                                json=new_vehicle,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        
        data = json.loads(response.data)
        self.assertIn('vehicle_id', data)
        self.assertIn('message', data)
        
        # Clean up - delete the test vehicle
        vehicle_id = data['vehicle_id']
        self.app.delete(f'/vehicles/{vehicle_id}')
    
    def test_add_vehicle_missing_fields(self):
        """Test adding a vehicle with missing required fields"""
        incomplete_vehicle = {
            'name': 'Test Vehicle'
            # Missing 'type' field
        }
        
        response = self.app.post('/vehicles',
                                json=incomplete_vehicle,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_fuel_logs(self):
        """Test getting fuel logs"""
        response = self.app.get('/fuel-logs')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('fuel_logs', data)
        self.assertIn('count', data)
        self.assertIsInstance(data['fuel_logs'], list)
        
        # Check structure of fuel logs
        if data['fuel_logs']:
            log = data['fuel_logs'][0]
            self.assertIn('id', log)
            self.assertIn('vehicle_id', log)
            self.assertIn('log_date', log)
            self.assertIn('km_driven', log)
            self.assertIn('fuel_used', log)
            self.assertIn('efficiency', log)
    
    def test_get_fuel_logs_with_vehicle_filter(self):
        """Test getting fuel logs filtered by vehicle"""
        response = self.app.get('/fuel-logs?vehicle_id=1')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('fuel_logs', data)
        
        # Check that all returned logs are for vehicle 1
        for log in data['fuel_logs']:
            self.assertEqual(log['vehicle_id'], 1)
    
    def test_add_fuel_log(self):
        """Test adding a new fuel log"""
        # First get a valid vehicle ID
        vehicles_response = self.app.get('/vehicles')
        vehicles_data = json.loads(vehicles_response.data)
        
        if vehicles_data['vehicles']:
            vehicle_id = vehicles_data['vehicles'][0]['id']
            
            new_log = {
                'vehicle_id': vehicle_id,
                'log_date': datetime.now().strftime('%Y-%m-%d'),
                'km_driven': 100.5,
                'fuel_used': 12.8,
                'cost': 22.40,
                'notes': 'Test log entry'
            }
            
            response = self.app.post('/fuel-logs',
                                    json=new_log,
                                    content_type='application/json')
            
            self.assertEqual(response.status_code, 201)
            
            data = json.loads(response.data)
            self.assertIn('log_id', data)
            self.assertIn('message', data)
            
            # Clean up - delete the test log
            log_id = data['log_id']
            self.app.delete(f'/fuel-logs/{log_id}')
    
    def test_add_fuel_log_invalid_vehicle(self):
        """Test adding a fuel log for a non-existent vehicle"""
        new_log = {
            'vehicle_id': 999999,
            'log_date': datetime.now().strftime('%Y-%m-%d'),
            'km_driven': 100.5,
            'fuel_used': 12.8
        }
        
        response = self.app.post('/fuel-logs',
                                json=new_log,
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_stats(self):
        """Test getting statistics"""
        response = self.app.get('/stats')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('overall_stats', data)
        self.assertIn('vehicle_stats', data)
        
        # Check overall stats structure
        overall = data['overall_stats']
        self.assertIn('total_vehicles', overall)
        self.assertIn('total_logs', overall)
        self.assertIn('total_km', overall)
        self.assertIn('total_fuel', overall)
        self.assertIn('avg_efficiency', overall)
        
        # Check vehicle stats structure
        vehicle_stats = data['vehicle_stats']
        self.assertIsInstance(vehicle_stats, list)
        
        if vehicle_stats:
            vehicle_stat = vehicle_stats[0]
            self.assertIn('name', vehicle_stat)
            self.assertIn('type', vehicle_stat)
            self.assertIn('total_km', vehicle_stat)
            self.assertIn('total_fuel', vehicle_stat)
    
    def test_fuel_prediction(self):
        """Test fuel consumption prediction"""
        response = self.app.get('/predict?km=100')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('kilometers', data)
        self.assertIn('predicted_fuel', data)
        self.assertIn('model_score', data)
        self.assertIn('training_samples', data)
        
        # Check data types
        self.assertEqual(data['kilometers'], 100)
        self.assertIsInstance(data['predicted_fuel'], (int, float))
        self.assertIsInstance(data['model_score'], (int, float))
        self.assertIsInstance(data['training_samples'], int)
    
    def test_fuel_prediction_invalid_km(self):
        """Test fuel prediction with invalid kilometers"""
        response = self.app.get('/predict?km=-10')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_fuel_prediction_missing_km(self):
        """Test fuel prediction without km parameter"""
        response = self.app.get('/predict')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_anomaly_detection(self):
        """Test anomaly detection"""
        response = self.app.get('/detect-anomalies')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('anomalies', data)
        self.assertIn('total_records_analyzed', data)
        self.assertIn('anomalies_found', data)
        self.assertIn('contamination_rate', data)
        
        # Check data types
        self.assertIsInstance(data['anomalies'], list)
        self.assertIsInstance(data['total_records_analyzed'], int)
        self.assertIsInstance(data['anomalies_found'], int)
        self.assertIsInstance(data['contamination_rate'], (int, float))
    
    def test_404_error(self):
        """Test 404 error handling"""
        response = self.app.get('/nonexistent-endpoint')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)

class DatabaseTestCase(unittest.TestCase):
    """Test database operations"""
    
    def test_database_connection(self):
        """Test that database connection works"""
        # Simple query to test connection
        result = execute_query("SELECT 1 as test", fetch_one=True)
        self.assertIsNotNone(result)
        self.assertEqual(result['test'], 1)
    
    def test_vehicles_table_exists(self):
        """Test that vehicles table exists and has expected structure"""
        result = execute_query("DESCRIBE vehicles", fetch_all=True)
        self.assertIsNotNone(result)
        
        # Check that required columns exist
        column_names = [col['Field'] for col in result]
        required_columns = ['id', 'name', 'type', 'license_plate', 'year', 'make', 'model']
        
        for col in required_columns:
            self.assertIn(col, column_names)
    
    def test_fuel_logs_table_exists(self):
        """Test that fuel_logs table exists and has expected structure"""
        result = execute_query("DESCRIBE fuel_logs", fetch_all=True)
        self.assertIsNotNone(result)
        
        # Check that required columns exist
        column_names = [col['Field'] for col in result]
        required_columns = ['id', 'vehicle_id', 'log_date', 'km_driven', 'fuel_used', 'cost', 'notes']
        
        for col in required_columns:
            self.assertIn(col, column_names)

if __name__ == '__main__':
    print("Running FleetFuel360 Unit Tests")
    print("=" * 40)
    print("Make sure the database is initialized and the app is configured correctly.")
    print()
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(FleetFuel360TestCase))
    suite.addTest(unittest.makeSuite(DatabaseTestCase))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print results
    print("\n" + "=" * 40)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed:")
        for failure in result.failures:
            print(f"  FAIL: {failure[0]}")
        for error in result.errors:
            print(f"  ERROR: {error[0]}")
    
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 40)
