"""
Dashboard View
Flask view to render the main dashboard
"""

from flask import Blueprint, render_template, request, current_app
from datetime import datetime, timedelta

# Create Blueprint
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    """Render the main dashboard"""
    
    # Get query parameters for default settings
    vehicle_id = request.args.get('vehicle_id', 'all')
    days_back = request.args.get('days_back', type=int, default=30)
    
    # Calculate date range for display
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Context data for the template
    context = {
        'title': 'FleetFuel360 Dashboard',
        'current_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'selected_vehicle': vehicle_id,
        'days_back': days_back,
        'date_range': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        },
        'api_base_url': '/api'
    }
    
    return render_template('dashboard.html', **context)

@dashboard_bp.route('/vehicle/<vehicle_id>')
def vehicle_detail(vehicle_id):
    """Render vehicle-specific dashboard"""
    
    days_back = request.args.get('days_back', type=int, default=30)
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    context = {
        'title': f'FleetFuel360 - {vehicle_id}',
        'current_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'selected_vehicle': vehicle_id,
        'days_back': days_back,
        'date_range': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        },
        'api_base_url': '/api',
        'is_vehicle_specific': True
    }
    
    return render_template('dashboard.html', **context)

@dashboard_bp.route('/executive')
def executive_dashboard():
    """Render executive dashboard"""
    
    days_back = request.args.get('days_back', type=int, default=30)
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    context = {
        'title': 'FleetFuel360 Executive Dashboard',
        'current_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'days_back': days_back,
        'date_range': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        },
        'api_base_url': '/api',
        'is_executive': True
    }
    
    return render_template('executive_dashboard.html', **context)

@dashboard_bp.route('/reports')
def reports():
    """Render reports dashboard"""
    return render_template('reports.html', title='FleetFuel360 Reports')

# Error handlers for the blueprint
@dashboard_bp.errorhandler(404)
def not_found(error):
    return render_template('dashboard.html', 
                         title='FleetFuel360 Dashboard',
                         error_message='Page not found'), 404

@dashboard_bp.errorhandler(500)
def internal_error(error):
    return render_template('dashboard.html',
                         title='FleetFuel360 Dashboard', 
                         error_message='Internal server error'), 500
