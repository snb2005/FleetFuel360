"""
FleetFuel360 Simple Application Launcher
Simplified version for demonstration purposes
"""

import os
import sys
from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.config import config
from backend.routes.api import api_bp
from frontend.dashboard_view import dashboard_bp

def create_app(config_name='development'):
    """Create and configure Flask application"""
    app = Flask(__name__,
                template_folder='frontend/templates',
                static_folder='frontend/static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize CORS for API access
    CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])
    
    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(dashboard_bp)
    
    # Add executive dashboard route
    @app.route('/executive')
    def executive_dashboard():
        """Serve executive dashboard"""
        return render_template('executive_dashboard.html')
    
    # Add PWA routes
    @app.route('/manifest.json')
    def manifest():
        """Serve PWA manifest"""
        return send_from_directory('frontend/static', 'manifest.json', mimetype='application/json')
    
    @app.route('/sw.js')
    def service_worker():
        """Serve service worker"""
        return send_from_directory('frontend/static', 'sw.js', mimetype='application/javascript')
    
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
    
    # Favicon route
    @app.route('/favicon.ico')
    def favicon():
        return app.send_static_file('favicon.ico')
    
    return app

if __name__ == '__main__':
    """Run the FleetFuel360 application"""
    
    print(f"""
🚛 FleetFuel360 - Advanced Fleet Analytics Platform
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 Dashboard:     http://127.0.0.1:5000
📊 Executive:     http://127.0.0.1:5000/executive  
🔧 API Health:    http://127.0.0.1:5000/api/health
📱 PWA Manifest:  http://127.0.0.1:5000/manifest.json

🚀 Features:
   ✓ Real-time Analytics & Alerts
   ✓ ML-Powered Anomaly Detection
   ✓ Predictive Maintenance
   ✓ Geospatial Route Optimization
   ✓ Cost Analysis & ROI Tracking
   ✓ Progressive Web App (PWA)
   ✓ Industry-Specific Modules
   ✓ Executive Business Intelligence
   ✓ Command Line Interface

💡 Try the CLI: python cli.py --help
📖 Documentation: README.md
🎯 Enhancement Roadmap: ENHANCEMENT_ROADMAP.md

Starting server...
    """)
    
    # Create Flask application
    app = create_app('development')
    
    # Start the application
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)
