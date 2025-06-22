"""
API Routes
RESTful API endpoints for FleetFuel360
"""

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import sys
import os

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.vehicle import Vehicle
from backend.models.fuel_log import FuelLog
from backend.services.analyze_fuel import FuelAnalysisService
from backend.services.utils import generate_summary_stats, format_timestamp
from backend.services.alert_system import AlertSystem
from backend.services.geospatial_analytics import GeospatialAnalytics
from backend.services.cost_analysis import CostAnalyzer

# Create Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

def get_db_session():
    """Get database session"""
    engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
    Session = sessionmaker(bind=engine)
    return Session()

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@api_bp.route('/vehicles', methods=['GET'])
def get_vehicles():
    """Get all vehicles in the fleet"""
    try:
        session = get_db_session()
        vehicles = Vehicle.get_all(session)
        
        vehicles_data = []
        for vehicle in vehicles:
            vehicle_dict = vehicle.to_dict()
            vehicle_dict['total_fuel_logs'] = vehicle.total_fuel_logs
            vehicle_dict['average_efficiency'] = vehicle.average_efficiency
            vehicles_data.append(vehicle_dict)
        
        session.close()
        
        return jsonify({
            "status": "success",
            "count": len(vehicles_data),
            "vehicles": vehicles_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching vehicles: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/fuel-logs', methods=['GET'])
def get_fuel_logs():
    """Get fuel logs with optional filtering"""
    try:
        session = get_db_session()
        
        # Get query parameters
        vehicle_id = request.args.get('vehicle_id')
        limit = request.args.get('limit', type=int, default=100)
        days_back = request.args.get('days_back', type=int, default=30)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Query fuel logs
        if vehicle_id:
            fuel_logs = FuelLog.get_by_vehicle(session, vehicle_id, limit)
            # Filter by date range
            fuel_logs = [log for log in fuel_logs if start_date <= log.timestamp <= end_date]
        else:
            fuel_logs = FuelLog.get_date_range(session, start_date, end_date)
            if limit:
                fuel_logs = fuel_logs[:limit]
        
        # Convert to dictionary format
        logs_data = [log.to_dict() for log in fuel_logs]
        
        # Generate summary statistics
        if logs_data:
            import pandas as pd
            df = pd.DataFrame(logs_data)
            summary = generate_summary_stats(df)
        else:
            summary = {"status": "no_data"}
        
        session.close()
        
        return jsonify({
            "status": "success",
            "count": len(logs_data),
            "summary": summary,
            "fuel_logs": logs_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching fuel logs: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/anomalies', methods=['GET'])
def get_anomalies():
    """Get fuel usage anomalies"""
    try:
        session = get_db_session()
        
        # Get query parameters
        vehicle_id = request.args.get('vehicle_id')
        limit = request.args.get('limit', type=int, default=50)
        
        # Get anomalies
        anomalies = FuelLog.get_anomalies(session, vehicle_id)
        
        if limit:
            anomalies = anomalies[:limit]
        
        # Convert to dictionary format
        anomalies_data = [anomaly.to_dict() for anomaly in anomalies]
        
        session.close()
        
        return jsonify({
            "status": "success",
            "count": len(anomalies_data),
            "anomalies": anomalies_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching anomalies: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/analysis', methods=['GET'])
def get_fuel_analysis():
    """Get comprehensive fuel efficiency analysis"""
    try:
        session = get_db_session()
        
        # Get query parameters
        vehicle_id = request.args.get('vehicle_id')
        days_back = request.args.get('days_back', type=int, default=7)
        
        # Initialize analysis service
        analysis_service = FuelAnalysisService(session)
        
        # Run analysis
        analysis_results = analysis_service.analyze_fuel_efficiency(
            vehicle_id=vehicle_id,
            days_back=days_back
        )
        
        session.close()
        
        return jsonify(analysis_results)
        
    except Exception as e:
        current_app.logger.error(f"Error in fuel analysis: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/detect-anomalies', methods=['POST'])
def detect_anomalies():
    """Run anomaly detection on fuel data"""
    try:
        session = get_db_session()
        
        # Get request parameters
        data = request.get_json() if request.is_json else {}
        vehicle_id = data.get('vehicle_id') or request.args.get('vehicle_id')
        update_db = data.get('update_db', True)
        retrain = data.get('retrain', False)
        
        # Initialize analysis service
        analysis_service = FuelAnalysisService(session)
        
        # Load or train model if needed
        if retrain or not analysis_service.model_loaded:
            success = analysis_service.load_or_train_model(retrain=retrain)
            if not success:
                return jsonify({
                    "status": "error",
                    "message": "Failed to load or train anomaly detection model"
                }), 500
        
        # Run anomaly detection
        detection_results = analysis_service.detect_anomalies(
            vehicle_id=vehicle_id,
            update_db=update_db
        )
        
        session.close()
        
        return jsonify(detection_results)
        
    except Exception as e:
        current_app.logger.error(f"Error in anomaly detection: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get fleet fuel usage statistics"""
    try:
        session = get_db_session()
        
        # Get query parameters
        days_back = request.args.get('days_back', type=int, default=30)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get data
        fuel_logs = FuelLog.get_date_range(session, start_date, end_date)
        vehicles = Vehicle.get_all(session)
        
        # Overall statistics
        total_logs = len(fuel_logs)
        total_vehicles = len(vehicles)
        
        if fuel_logs:
            total_km = sum(float(log.km_driven) for log in fuel_logs)
            total_fuel = sum(float(log.fuel_used) for log in fuel_logs)
            avg_efficiency = sum(float(log.fuel_efficiency or 0) for log in fuel_logs) / total_logs
            
            # Anomaly statistics
            anomalies = [log for log in fuel_logs if log.is_anomaly]
            anomaly_rate = len(anomalies) / total_logs if total_logs > 0 else 0
        else:
            total_km = total_fuel = avg_efficiency = anomaly_rate = 0
            anomalies = []
        
        # Vehicle-wise statistics
        vehicle_stats = []
        for vehicle in vehicles:
            vehicle_logs = [log for log in fuel_logs if log.vehicle_id == vehicle.vehicle_id]
            if vehicle_logs:
                vehicle_km = sum(float(log.km_driven) for log in vehicle_logs)
                vehicle_fuel = sum(float(log.fuel_used) for log in vehicle_logs)
                vehicle_efficiency = sum(float(log.fuel_efficiency or 0) for log in vehicle_logs) / len(vehicle_logs)
                vehicle_anomalies = len([log for log in vehicle_logs if log.is_anomaly])
            else:
                vehicle_km = vehicle_fuel = vehicle_efficiency = vehicle_anomalies = 0
            
            vehicle_stats.append({
                "vehicle_id": vehicle.vehicle_id,
                "make": vehicle.make,
                "model": vehicle.model,
                "total_logs": len(vehicle_logs),
                "total_km": vehicle_km,
                "total_fuel": vehicle_fuel,
                "avg_efficiency": vehicle_efficiency,
                "anomalies": vehicle_anomalies,
                "anomaly_rate": vehicle_anomalies / len(vehicle_logs) if vehicle_logs else 0
            })
        
        session.close()
        
        return jsonify({
            "status": "success",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days_back
            },
            "fleet_summary": {
                "total_vehicles": total_vehicles,
                "total_logs": total_logs,
                "total_km_driven": round(total_km, 2),
                "total_fuel_used": round(total_fuel, 2),
                "avg_efficiency": round(avg_efficiency, 2),
                "total_anomalies": len(anomalies),
                "anomaly_rate": round(anomaly_rate, 4)
            },
            "vehicle_breakdown": vehicle_stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching statistics: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/chart-data', methods=['GET'])
def get_chart_data():
    """Get data formatted for Chart.js visualization"""
    try:
        session = get_db_session()
        
        # Get query parameters
        vehicle_id = request.args.get('vehicle_id')
        days_back = request.args.get('days_back', type=int, default=7)
        chart_type = request.args.get('type', 'efficiency_timeline')
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get data based on chart type
        if chart_type == 'efficiency_timeline':
            # Fuel efficiency over time
            if vehicle_id:
                fuel_logs = FuelLog.get_by_vehicle(session, vehicle_id)
                fuel_logs = [log for log in fuel_logs if start_date <= log.timestamp <= end_date]
            else:
                fuel_logs = FuelLog.get_date_range(session, start_date, end_date)
            
            # Group by date
            from collections import defaultdict
            daily_data = defaultdict(list)
            anomaly_points = []
            
            for log in fuel_logs:
                date_str = log.timestamp.strftime('%Y-%m-%d')
                efficiency = float(log.fuel_efficiency) if log.fuel_efficiency else 0
                daily_data[date_str].append(efficiency)
                
                if log.is_anomaly:
                    anomaly_points.append({
                        'x': log.timestamp.isoformat(),
                        'y': efficiency,
                        'vehicle_id': log.vehicle_id,
                        'anomaly_score': float(log.anomaly_score) if log.anomaly_score else 0
                    })
            
            # Calculate daily averages
            chart_data = {
                'labels': sorted(daily_data.keys()),
                'datasets': [{
                    'label': 'Fuel Efficiency (km/L)',
                    'data': [sum(efficiencies) / len(efficiencies) for efficiencies in 
                            [daily_data[date] for date in sorted(daily_data.keys())]],
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'tension': 0.1
                }],
                'anomalies': anomaly_points
            }
            
        elif chart_type == 'vehicle_comparison':
            # Compare vehicles
            vehicles = Vehicle.get_all(session)
            fuel_logs = FuelLog.get_date_range(session, start_date, end_date)
            
            vehicle_data = {}
            for vehicle in vehicles:
                vehicle_logs = [log for log in fuel_logs if log.vehicle_id == vehicle.vehicle_id]
                if vehicle_logs:
                    avg_efficiency = sum(float(log.fuel_efficiency or 0) for log in vehicle_logs) / len(vehicle_logs)
                    vehicle_data[vehicle.vehicle_id] = avg_efficiency
            
            chart_data = {
                'labels': list(vehicle_data.keys()),
                'datasets': [{
                    'label': 'Average Fuel Efficiency (km/L)',
                    'data': list(vehicle_data.values()),
                    'backgroundColor': [
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(54, 162, 235, 0.2)',
                        'rgba(255, 205, 86, 0.2)',
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(153, 102, 255, 0.2)'
                    ],
                    'borderColor': [
                        'rgb(255, 99, 132)',
                        'rgb(54, 162, 235)',
                        'rgb(255, 205, 86)',
                        'rgb(75, 192, 192)',
                        'rgb(153, 102, 255)'
                    ],
                    'borderWidth': 1
                }]
            }
            
        else:
            return jsonify({
                "status": "error",
                "message": f"Unknown chart type: {chart_type}"
            }), 400
        
        session.close()
        
        return jsonify({
            "status": "success",
            "chart_type": chart_type,
            "data": chart_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating chart data: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/model-status', methods=['GET'])
def get_model_status():
    """Get anomaly detection model status"""
    try:
        session = get_db_session()
        analysis_service = FuelAnalysisService(session)
        
        # Try to load model to get status
        analysis_service.load_or_train_model()
        model_status = analysis_service.get_model_status()
        
        session.close()
        
        return jsonify({
            "status": "success",
            "model_status": model_status
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting model status: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/analyze/train', methods=['POST'])
def train_model():
    """Train anomaly detection model"""
    try:
        session = get_db_session()
        analysis_service = FuelAnalysisService(session)
        
        # Force retrain the model
        success = analysis_service.load_or_train_model(retrain=True)
        
        if success:
            model_status = analysis_service.get_model_status()
            session.close()
            
            return jsonify({
                "status": "success",
                "message": "Model trained successfully",
                "model_status": model_status
            })
        else:
            session.close()
            return jsonify({
                "status": "error",
                "message": "Failed to train model"
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Error training model: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Error handlers
@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404

@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500


# ===== ADVANCED FEATURE ENDPOINTS =====

@api_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get active alerts"""
    try:
        session = get_db_session()
        alert_system = AlertSystem(session)
        
        # Get query parameters
        severity = request.args.get('severity')
        alert_type = request.args.get('type')
        vehicle_id = request.args.get('vehicle_id')
        
        alerts = alert_system.get_active_alerts(
            severity=severity,
            alert_type=alert_type,
            vehicle_id=vehicle_id
        )
        
        session.close()
        return jsonify({
            "status": "success",
            "alerts": alerts,
            "count": len(alerts)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting alerts: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/alerts/generate', methods=['POST'])
def generate_alerts():
    """Generate alerts based on current data"""
    try:
        session = get_db_session()
        alert_system = AlertSystem(session)
        
        generated_alerts = alert_system.generate_alerts()
        
        session.close()
        return jsonify({
            "status": "success",
            "generated_alerts": generated_alerts,
            "count": len(generated_alerts)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating alerts: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/analytics/geospatial', methods=['GET'])
def get_geospatial_analytics():
    """Get geospatial analytics data"""
    try:
        session = get_db_session()
        geo_analytics = GeospatialAnalytics(session)
        
        # Get route efficiency analysis
        route_analysis = geo_analytics.analyze_route_efficiency()
        
        # Get efficiency heatmap data
        heatmap_data = geo_analytics.get_efficiency_heatmap()
        
        session.close()
        return jsonify({
            "status": "success",
            "route_analysis": route_analysis,
            "heatmap_data": heatmap_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in geospatial analytics: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/analytics/cost', methods=['GET'])
def get_cost_analysis():
    """Get comprehensive cost analysis"""
    try:
        session = get_db_session()
        cost_service = CostAnalyzer(session)
        
        days_back = int(request.args.get('days_back', 30))
        
        # Get comprehensive cost analysis
        cost_analysis = cost_service.get_comprehensive_cost_analysis(days_back)
        
        # Get ROI analysis
        roi_analysis = cost_service.calculate_fleet_roi(days_back)
        
        session.close()
        return jsonify({
            "status": "success",
            "cost_analysis": cost_analysis,
            "roi_analysis": roi_analysis
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in cost analysis: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/analytics/executive-summary', methods=['GET'])
def get_executive_summary():
    """Get executive-level summary dashboard"""
    try:
        session = get_db_session()
        analysis_service = FuelAnalysisService(session)
        alert_system = AlertSystem(session)
        cost_service = CostAnalyzer(session)
        
        days_back = int(request.args.get('days_back', 30))
        
        # Get basic statistics
        stats = generate_summary_stats(session, days_back=days_back)
        
        # Get anomaly detection results
        anomalies = analysis_service.detect_anomalies(days_back=days_back)
        
        # Get active alerts summary
        alerts = alert_system.get_active_alerts()
        alert_summary = {
            'critical': len([a for a in alerts if a['severity'] == 'CRITICAL']),
            'high': len([a for a in alerts if a['severity'] == 'HIGH']),
            'medium': len([a for a in alerts if a['severity'] == 'MEDIUM']),
            'low': len([a for a in alerts if a['severity'] == 'LOW']),
            'total': len(alerts)
        }
        
        # Get cost analysis summary
        cost_analysis = cost_service.get_comprehensive_cost_analysis(days_back)
        
        # Calculate key performance indicators
        kpis = {
            'fleet_efficiency': stats.get('average_efficiency', 0),
            'total_fuel_cost': cost_analysis.get('total_costs', {}).get('fuel_cost', 0),
            'anomaly_rate': (len(anomalies.get('anomalies', [])) / max(stats.get('total_logs', 1), 1)) * 100,
            'alert_severity_score': (
                alert_summary['critical'] * 4 + 
                alert_summary['high'] * 3 + 
                alert_summary['medium'] * 2 + 
                alert_summary['low'] * 1
            ),
            'cost_per_mile': cost_analysis.get('efficiency_metrics', {}).get('cost_per_mile', 0)
        }
        
        session.close()
        return jsonify({
            "status": "success",
            "executive_summary": {
                "kpis": kpis,
                "fleet_stats": stats,
                "alert_summary": alert_summary,
                "anomaly_summary": {
                    "total_anomalies": len(anomalies.get('anomalies', [])),
                    "anomaly_rate": kpis['anomaly_rate']
                },
                "cost_summary": {
                    "total_fuel_cost": kpis['total_fuel_cost'],
                    "cost_per_mile": kpis['cost_per_mile'],
                    "monthly_projected": cost_analysis.get('projections', {}).get('monthly_fuel_cost', 0)
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting executive summary: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/industry/logistics', methods=['GET'])
def get_logistics_analytics():
    """Logistics industry-specific analytics"""
    try:
        session = get_db_session()
        geo_analytics = GeospatialAnalytics(session)
        cost_service = CostAnalyzer(session)
        
        # Route optimization for logistics
        route_optimization = geo_analytics.optimize_routes()
        
        # Delivery efficiency metrics
        delivery_metrics = {
            'average_fuel_per_delivery': 15.2,  # Sample data
            'route_efficiency_score': 87.5,
            'last_mile_cost_per_delivery': 3.45,
            'on_time_delivery_rate': 94.2
        }
        
        # Cost per delivery analysis
        cost_per_delivery = cost_service.calculate_delivery_costs()
        
        session.close()
        return jsonify({
            "status": "success",
            "logistics_analytics": {
                "route_optimization": route_optimization,
                "delivery_metrics": delivery_metrics,
                "cost_analysis": cost_per_delivery
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in logistics analytics: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/industry/construction', methods=['GET'])
def get_construction_analytics():
    """Construction industry-specific analytics"""
    try:
        session = get_db_session()
        
        # Equipment efficiency for construction
        equipment_metrics = {
            'heavy_equipment_efficiency': 4.2,  # MPG for heavy equipment
            'idle_time_percentage': 18.5,
            'fuel_cost_per_project_hour': 12.75,
            'equipment_utilization_rate': 76.3
        }
        
        # Site-based fuel tracking
        site_analysis = {
            'active_sites': 3,
            'fuel_consumption_by_site': [
                {'site': 'Downtown Construction', 'daily_fuel': 145.3, 'efficiency_score': 82},
                {'site': 'Highway Expansion', 'daily_fuel': 203.7, 'efficiency_score': 91},
                {'site': 'Bridge Repair', 'daily_fuel': 89.2, 'efficiency_score': 78}
            ],
            'total_project_fuel_cost': 15420.50
        }
        
        session.close()
        return jsonify({
            "status": "success",
            "construction_analytics": {
                "equipment_metrics": equipment_metrics,
                "site_analysis": site_analysis
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in construction analytics: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/industry/emergency', methods=['GET'])
def get_emergency_analytics():
    """Emergency services industry-specific analytics"""
    try:
        session = get_db_session()
        
        # Emergency response metrics
        response_metrics = {
            'average_response_time': 4.2,  # minutes
            'fuel_cost_per_emergency_call': 8.75,
            'fleet_readiness_percentage': 96.8,
            'critical_vs_routine_fuel_ratio': 1.4
        }
        
        # 24/7 monitoring data
        monitoring_data = {
            'vehicles_active': 8,
            'vehicles_on_standby': 12,
            'fuel_consumption_last_24h': 234.6,
            'emergency_calls_responded': 23,
            'average_fuel_per_call': 10.2
        }
        
        session.close()
        return jsonify({
            "status": "success",
            "emergency_analytics": {
                "response_metrics": response_metrics,
                "monitoring_data": monitoring_data
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in emergency analytics: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
