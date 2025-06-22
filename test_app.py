#!/usr/bin/env python3
"""
Test script for FleetFuel360
"""

import os
import sys

# Set environment variables
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_DB'] = 'fleetfuel360'
os.environ['POSTGRES_USER'] = 'fleetfuel_user'
os.environ['POSTGRES_PASSWORD'] = 'fleetfuel123'

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports"""
    try:
        print("🧪 Testing imports...")
        
        # Test basic libraries
        import flask
        import sqlalchemy
        import pandas
        print("✅ Basic libraries imported")
        
        # Test config
        from backend.config import Config
        print("✅ Config imported")
        
        # Test models
        from backend.models.vehicle import Vehicle
        from backend.models.fuel_log import FuelLog
        print("✅ Models imported")
        
        # Test database connection
        from sqlalchemy import create_engine, text
        config = Config()
        engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM vehicles"))
            count = result.scalar()
            print(f"✅ Database connected: {count} vehicles")
        
        # Test routes
        from backend.routes.api import api_bp
        print("✅ API routes imported")
        
        from frontend.dashboard_view import dashboard_bp
        print("✅ Dashboard view imported")
        
        print("🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_creation():
    """Test Flask app creation"""
    try:
        print("\n🧪 Testing Flask app creation...")
        
        from app import create_app
        app = create_app()
        print("✅ Flask app created")
        
        # Test with test client
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/api/health')
            print(f"✅ Health endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"   Response: {data}")
            
            # Test vehicles endpoint
            response = client.get('/api/vehicles')
            print(f"✅ Vehicles endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"   Found {data.get('count', 0)} vehicles")
            
            # Test dashboard
            response = client.get('/')
            print(f"✅ Dashboard endpoint: {response.status_code}")
        
        print("🎉 App creation and testing successful!")
        return True
        
    except Exception as e:
        print(f"❌ App creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 FleetFuel360 Test Suite")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test app creation
        app_ok = test_app_creation()
        
        if app_ok:
            print("\n✅ All tests passed! Ready to run the application.")
            print("Run: python3 app.py")
        else:
            print("\n❌ App creation failed")
    else:
        print("\n❌ Import tests failed")
