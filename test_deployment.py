#!/usr/bin/env python3
"""
FleetFuel360 Deployment Test Script
Tests if the application is ready for deployment
"""

import os
import sys
import tempfile
import subprocess

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing Python imports...")
    
    try:
        # Test main app import
        from wsgi import app
        print("✅ Main application imports successfully")
        
        # Test database models
        from backend.models.vehicle import Vehicle
        from backend.models.fuel_log import FuelLog
        print("✅ Database models import successfully")
        
        # Test services
        from backend.services.analyze_fuel import FuelAnalysisService
        from backend.services.bi_reports import BusinessIntelligenceReports
        print("✅ Services import successfully")
        
        # Test configuration
        from backend.config import config
        print("✅ Configuration imports successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_requirements():
    """Test if all requirements are satisfied"""
    print("📦 Testing requirements...")
    
    try:
        # Test Flask
        import flask
        print(f"✅ Flask {flask.__version__}")
        
        # Test SQLAlchemy
        import sqlalchemy
        print(f"✅ SQLAlchemy {sqlalchemy.__version__}")
        
        # Test Pandas
        import pandas
        print(f"✅ Pandas {pandas.__version__}")
        
        # Test Scikit-learn
        import sklearn
        print(f"✅ Scikit-learn {sklearn.__version__}")
        
        # Test Gunicorn
        import gunicorn
        print(f"✅ Gunicorn {gunicorn.__version__}")
        
        return True
    except Exception as e:
        print(f"❌ Requirements error: {e}")
        return False

def test_configuration():
    """Test if configuration is valid"""
    print("⚙️ Testing configuration...")
    
    try:
        from backend.config import config
        
        # Test development config
        dev_config = config['development']
        print(f"✅ Development config: {dev_config}")
        
        # Test production config
        prod_config = config['production']
        print(f"✅ Production config: {prod_config}")
        
        # Test database URI format
        if 'postgresql://' in prod_config.SQLALCHEMY_DATABASE_URI:
            print("✅ Database URI format is correct")
        else:
            print("⚠️ Database URI format may need adjustment")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_deployment_files():
    """Test if deployment files exist and are valid"""
    print("📁 Testing deployment files...")
    
    files_to_check = [
        'render.yaml',
        'build.sh',
        'wsgi.py',
        'Procfile',
        'requirements.txt'
    ]
    
    all_good = True
    for file in files_to_check:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            all_good = False
    
    # Check if build.sh is executable
    if os.path.exists('build.sh'):
        if os.access('build.sh', os.X_OK):
            print("✅ build.sh is executable")
        else:
            print("⚠️ build.sh is not executable (run: chmod +x build.sh)")
    
    return all_good

def test_wsgi_app():
    """Test if WSGI app can be created"""
    print("🌐 Testing WSGI application...")
    
    try:
        from wsgi import app
        
        # Test if app is a Flask instance
        if hasattr(app, 'run'):
            print("✅ WSGI app is a valid Flask instance")
        else:
            print("❌ WSGI app is not a valid Flask instance")
            return False
        
        # Test if app has routes
        if len(app.url_map._rules) > 0:
            print(f"✅ App has {len(app.url_map._rules)} routes configured")
        else:
            print("⚠️ App has no routes configured")
        
        return True
    except Exception as e:
        print(f"❌ WSGI app error: {e}")
        return False

def main():
    """Run all deployment tests"""
    print("🚀 FleetFuel360 Deployment Readiness Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_requirements,
        test_configuration,
        test_deployment_files,
        test_wsgi_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print()
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        print("-" * 30)
    
    print()
    print("📊 DEPLOYMENT READINESS SUMMARY")
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your app is ready for Render deployment.")
        print()
        print("Next steps:")
        print("1. Push your code to GitHub")
        print("2. Connect your GitHub repo to Render")
        print("3. Render will automatically deploy using render.yaml")
        return True
    else:
        print("⚠️ Some tests failed. Please fix the issues before deploying.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
