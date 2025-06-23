"""
FleetFuel360 Main Application
Flask application entry point with advanced features and real-time capabilities
"""

import os
import sys
from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.config import config
from backend.routes.api import api_bp
from frontend.dashboard_view import dashboard_bp
from backend.services.realtime_service import create_realtime_service, simulate_real_time_events

def create_app(config_name='development'):
    """
    Create and configure Flask application with advanced features
    
    Args:
        config_name (str): Configuration environment name
        
    Returns:
        Flask: Configured Flask application with real-time capabilities
    """
    app = Flask(__name__,
                template_folder='frontend/templates',
                static_folder='frontend/static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize CORS for API access
    CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])
    
    # Initialize database session factory
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    SessionFactory = sessionmaker(bind=engine)
    
    # Initialize real-time service with WebSocket support
    realtime_service = create_realtime_service(app, SessionFactory)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(dashboard_bp)
    
    # Add PWA routes
    @app.route('/manifest.json')
    def manifest():
        """Serve PWA manifest"""
        return send_from_directory('frontend/static', 'manifest.json', mimetype='application/json')
    
    @app.route('/sw.js')
    def service_worker():
        """Serve service worker"""
        return send_from_directory('frontend/static', 'sw.js', mimetype='application/javascript')
    
    @app.route('/offline.html')
    def offline():
        """Serve offline page"""
        return render_template('offline.html')
    
    # Add health check for load balancers
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'version': '2.0.0',
            'features': [
                'real_time_analytics',
                'predictive_maintenance',
                'geospatial_analytics',
                'cost_optimization',
                'progressive_web_app'
            ]
        })
    
    # Add system info endpoint
    @app.route('/system-info')
    def system_info():
        """System information for monitoring"""
        try:
            session = SessionFactory()
            from backend.models.vehicle import Vehicle
            from backend.models.fuel_log import FuelLog
            
            vehicle_count = session.query(Vehicle).count()
            log_count = session.query(FuelLog).count()
            session.close()
            
            return jsonify({
                'total_vehicles': vehicle_count,
                'total_fuel_logs': log_count,
                'real_time_connections': len(realtime_service.active_connections),
                'monitoring_active': realtime_service.monitoring_active
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Initialize real-time monitoring after app setup
    def initialize_realtime():
        """Initialize real-time services"""
        if not hasattr(app, '_realtime_initialized'):
            realtime_service.start_monitoring()
            app._realtime_initialized = True
            
            # Start demo event simulation in development
            if app.config.get('DEBUG', False):
                simulate_real_time_events(realtime_service)
    
    # Schedule initialization to run after first request using new Flask pattern
    @app.before_request
    def setup_realtime():
        if not hasattr(app, '_realtime_initialized'):
            initialize_realtime()
    
    # Store realtime service in app context for access
    app.realtime_service = realtime_service
    
    return app

def main():
    """
    Main application entry point
    """
    print("🚀 Starting FleetFuel360 Application...")
    print("=" * 50)
    
    # Get configuration from environment
    config_name = os.getenv('FLASK_ENV', 'development')
    
    # Create Flask app
    app = create_app(config_name)
    
    # Print startup information
    print(f"📊 Configuration: {config_name}")
    print(f"📍 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"🔧 Debug Mode: {app.config['DEBUG']}")
    print("=" * 50)
    
    # Database initialization check
    print("🔍 Checking database connection...")
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM vehicles"))
            vehicle_count = result.scalar()
            print(f"✅ Database connected. Found {vehicle_count} vehicles.")
    except Exception as e:
        print(f"⚠️  Database connection warning: {e}")
        print("💡 Run 'python backend/db/init_db.py' to initialize the database")
    
    print("=" * 50)
    print("🌐 Application URLs:")
    print("   Dashboard: http://localhost:5000/")
    print("   API Health: http://localhost:5000/api/health")
    print("   API Docs: http://localhost:5000/api/")
    print("=" * 50)
    
    # Start the application
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=app.config['DEBUG'],
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 FleetFuel360 application stopped.")
    except Exception as e:
        print(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    """
    Run the FleetFuel360 application with advanced features
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='FleetFuel360 - Advanced Fleet Analytics Platform')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', default='development', help='Configuration environment')
    parser.add_argument('--generate-demo', action='store_true', help='Generate demo data on startup')
    
    args = parser.parse_args()
    
    # Create Flask application
    app = create_app(args.config)
    
    # Generate demo data if requested
    if args.generate_demo:
        print("🚀 Generating demo data...")
        try:
            from backend.services.demo_data_generator import DemoDataGenerator
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            Session = sessionmaker(bind=engine)
            session = Session()
            
            generator = DemoDataGenerator(session)
            result = generator.populate_database(vehicle_count=25, days=60)
            
            print(f"✅ Generated {result['vehicles_added']} vehicles and {result['fuel_logs_added']} fuel logs")
            session.close()
        except Exception as e:
            print(f"❌ Error generating demo data: {e}")
    
    print(f"""
🚛 FleetFuel360 - Advanced Fleet Analytics Platform
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 Dashboard:     http://{args.host}:{args.port}
📊 Executive:     http://{args.host}:{args.port}/executive
🔧 API Health:    http://{args.host}:{args.port}/api/health
📱 PWA Manifest:  http://{args.host}:{args.port}/manifest.json

🚀 Features:
   ✓ Real-time Analytics & Alerts
   ✓ ML-Powered Anomaly Detection
   ✓ Predictive Maintenance
   ✓ Geospatial Route Optimization
   ✓ Cost Analysis & ROI Tracking
   ✓ Progressive Web App (PWA)
   ✓ WebSocket Real-time Updates
   ✓ Industry-Specific Modules
   ✓ Executive Business Intelligence
   ✓ Command Line Interface

💡 Try the CLI: python cli.py --help
📖 Documentation: README.md
🎯 Enhancement Roadmap: ENHANCEMENT_ROADMAP.md

Starting server...
    """)
    
    # Start the application with SocketIO support
    socketio = app.realtime_service.socketio
    socketio.run(app, 
                host=args.host, 
                port=args.port, 
                debug=args.debug,
                allow_unsafe_werkzeug=True)
