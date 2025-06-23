"""
FleetFuel360 Production Entry Point
Simple entry point for deployment on Render
"""

import os
from app import create_app

# Get configuration from environment
config_name = os.getenv('FLASK_ENV', 'production')

# Create Flask application instance
app = create_app(config_name)

if __name__ == '__main__':
    # This is only used for local development
    # In production, gunicorn will import the 'app' object
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
