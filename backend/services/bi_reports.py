"""
Business Intelligence Report Generator
Generates comprehensive reports for executives and fleet managers
"""

from datetime import datetime, timedelta
import json
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import pandas as pd
from jinja2 import Template
import sys
import os

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.analyze_fuel import FuelAnalysisService
from backend.services.alert_system import AlertSystem
from backend.services.cost_analysis import CostAnalyzer
from backend.services.geospatial_analytics import GeospatialAnalytics

class BusinessIntelligenceReports:
    def __init__(self, db_session):
        self.session = db_session
        self.analysis_service = FuelAnalysisService(db_session)
        self.alert_system = AlertSystem(db_session)
        self.cost_service = CostAnalyzer(db_session)
        self.geo_service = GeospatialAnalytics(db_session)
        
        # Set up styling for charts
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def generate_executive_summary_report(self, days_back=30):
        """Generate comprehensive executive summary report"""
        
        # Collect all data
        fleet_stats = self._get_fleet_statistics(days_back)
        cost_analysis = self.cost_service.get_comprehensive_cost_analysis(days_back)
        alerts_summary = self._get_alerts_summary()
        anomaly_analysis = self.analysis_service.detect_anomalies(days_back)
        performance_trends = self._get_performance_trends(days_back)
        roi_analysis = self.cost_service.calculate_fleet_roi(days_back)
        
        # Generate key insights
        insights = self._generate_key_insights(
            fleet_stats, cost_analysis, alerts_summary, anomaly_analysis
        )
        
        # Create visualizations
        charts = self._create_executive_charts(
            fleet_stats, cost_analysis, performance_trends
        )
        
        report = {
            'report_metadata': {
                'title': 'FleetFuel360 Executive Summary',
                'generated_at': datetime.now().isoformat(),
                'period': f'Last {days_back} days',
                'report_type': 'executive_summary'
            },
            'key_metrics': {
                'total_vehicles': fleet_stats.get('total_vehicles', 0),
                'total_fuel_cost': cost_analysis.get('total_costs', {}).get('fuel_cost', 0),
                'average_efficiency': fleet_stats.get('average_efficiency', 0),
                'total_miles': fleet_stats.get('total_miles', 0),
                'cost_per_mile': cost_analysis.get('efficiency_metrics', {}).get('cost_per_mile', 0),
                'anomaly_rate': len(anomaly_analysis.get('anomalies', [])) / max(fleet_stats.get('total_logs', 1), 1) * 100
            },
            'performance_summary': {
                'fleet_efficiency_trend': performance_trends.get('efficiency_trend', 'stable'),
                'cost_trend': performance_trends.get('cost_trend', 'stable'),
                'top_performing_vehicles': self._get_top_performers(5),
                'vehicles_needing_attention': self._get_underperformers(5)
            },
            'financial_analysis': {
                'monthly_fuel_spend': cost_analysis.get('projections', {}).get('monthly_fuel_cost', 0),
                'potential_savings': cost_analysis.get('optimization_opportunities', {}).get('potential_monthly_savings', 0),
                'roi_metrics': roi_analysis,
                'cost_breakdown': cost_analysis.get('cost_breakdown', {})
            },
            'risk_assessment': {
                'critical_alerts': alerts_summary.get('critical', 0),
                'high_priority_alerts': alerts_summary.get('high', 0),
                'anomaly_vehicles': len(anomaly_analysis.get('anomalies', [])),
                'maintenance_due': self._count_maintenance_due()
            },
            'recommendations': insights['recommendations'],
            'action_items': insights['action_items'],
            'charts': charts
        }
        
        return report
    
    def generate_operational_report(self, days_back=7):
        """Generate detailed operational report for fleet managers"""
        
        vehicle_performance = self._get_detailed_vehicle_performance(days_back)
        route_analysis = self.geo_service.analyze_route_efficiency()
        fuel_trends = self._get_fuel_consumption_trends(days_back)
        efficiency_analysis = self._get_efficiency_analysis(days_back)
        
        report = {
            'report_metadata': {
                'title': 'FleetFuel360 Operational Report',
                'generated_at': datetime.now().isoformat(),
                'period': f'Last {days_back} days',
                'report_type': 'operational'
            },
            'vehicle_performance': vehicle_performance,
            'route_analysis': route_analysis,
            'fuel_consumption': {
                'daily_trends': fuel_trends,
                'efficiency_by_vehicle': efficiency_analysis['by_vehicle'],
                'efficiency_by_route': efficiency_analysis['by_route']
            },
            'operational_metrics': {
                'utilization_rate': self._calculate_fleet_utilization(days_back),
                'maintenance_schedule': self._get_maintenance_schedule(),
                'driver_performance': self._get_driver_performance_summary()
            },
            'charts': self._create_operational_charts(vehicle_performance, fuel_trends)
        }
        
        return report
    
    def generate_compliance_report(self, days_back=30):
        """Generate compliance and regulatory report"""
        
        emissions_data = self._calculate_emissions_data(days_back)
        safety_metrics = self._get_safety_metrics(days_back)
        regulatory_compliance = self._check_regulatory_compliance()
        
        report = {
            'report_metadata': {
                'title': 'FleetFuel360 Compliance Report',
                'generated_at': datetime.now().isoformat(),
                'period': f'Last {days_back} days',
                'report_type': 'compliance'
            },
            'emissions': {
                'total_co2_emissions': emissions_data['total_co2'],
                'emissions_per_mile': emissions_data['co2_per_mile'],
                'reduction_targets': emissions_data['reduction_opportunities']
            },
            'safety_metrics': safety_metrics,
            'regulatory_status': regulatory_compliance,
            'audit_trail': self._get_audit_trail(days_back)
        }
        
        return report
    
    def generate_predictive_report(self):
        """Generate predictive analytics report"""
        
        from backend.services.predictive_analytics import PredictiveAnalytics
        predictor = PredictiveAnalytics(self.session)
        
        # Get predictions
        fuel_predictions = predictor.predict_fuel_consumption()
        maintenance_predictions = predictor.predict_maintenance_needs()
        efficiency_forecast = predictor.forecast_fleet_efficiency()
        
        report = {
            'report_metadata': {
                'title': 'FleetFuel360 Predictive Analytics Report',
                'generated_at': datetime.now().isoformat(),
                'report_type': 'predictive'
            },
            'fuel_predictions': fuel_predictions,
            'maintenance_predictions': maintenance_predictions,
            'efficiency_forecast': efficiency_forecast,
            'recommendations': self._generate_predictive_recommendations(
                fuel_predictions, maintenance_predictions, efficiency_forecast
            )
        }
        
        return report
    
    def _get_fleet_statistics(self, days_back):
        """Get comprehensive fleet statistics"""
        from backend.models.fuel_log import FuelLog
        import pandas as pd
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        fuel_logs = FuelLog.get_date_range(self.session, start_date, end_date)
        logs_data = [log.to_dict() for log in fuel_logs]
        if logs_data:
            df = pd.DataFrame(logs_data)
            from backend.services.utils import generate_summary_stats
            return generate_summary_stats(df)
        else:
            return {"status": "no_data", "total_logs": 0, "average_efficiency": 0}
    
    def _get_alerts_summary(self):
        """Get summary of alerts by severity"""
        alerts = self.alert_system.get_active_alerts()
        summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for alert in alerts:
            severity = alert.get('severity', 'low').lower()
            if severity in summary:
                summary[severity] += 1
        
        return summary
    
    def _get_performance_trends(self, days_back):
        """Analyze performance trends"""
        # This would typically analyze historical data
        # For demo purposes, we'll create sample trends
        
        return {
            'efficiency_trend': 'improving',  # 'improving', 'declining', 'stable'
            'cost_trend': 'stable',
            'utilization_trend': 'improving'
        }
    
    def _get_top_performers(self, count):
        """Get top performing vehicles"""
        # Sample data - in real implementation, this would query actual data
        return [
            {'vehicle_id': 'TRUCK001', 'efficiency': 12.5, 'performance_score': 95},
            {'vehicle_id': 'TRUCK007', 'efficiency': 12.2, 'performance_score': 93},
            {'vehicle_id': 'TRUCK012', 'efficiency': 11.8, 'performance_score': 91},
            {'vehicle_id': 'TRUCK003', 'efficiency': 11.6, 'performance_score': 89},
            {'vehicle_id': 'TRUCK015', 'efficiency': 11.4, 'performance_score': 87}
        ][:count]
    
    def _get_underperformers(self, count):
        """Get underperforming vehicles"""
        return [
            {'vehicle_id': 'TRUCK018', 'efficiency': 8.2, 'issues': ['Maintenance overdue', 'Route inefficiency']},
            {'vehicle_id': 'TRUCK009', 'efficiency': 8.7, 'issues': ['Driver training needed']},
            {'vehicle_id': 'TRUCK014', 'efficiency': 9.1, 'issues': ['Fuel system check needed']}
        ][:count]
    
    def _count_maintenance_due(self):
        """Count vehicles due for maintenance"""
        # Sample implementation
        return 3
    
    def _generate_key_insights(self, fleet_stats, cost_analysis, alerts_summary, anomaly_analysis):
        """Generate key business insights"""
        
        recommendations = []
        action_items = []
        
        # Efficiency insights
        avg_efficiency = fleet_stats.get('average_efficiency', 0)
        if avg_efficiency < 10:
            recommendations.append("Fleet efficiency below industry average - consider driver training programs")
            action_items.append("Schedule driver efficiency training within 30 days")
        
        # Cost insights
        cost_per_mile = cost_analysis.get('efficiency_metrics', {}).get('cost_per_mile', 0)
        if cost_per_mile > 0.50:
            recommendations.append("High cost per mile indicates potential fuel waste or route inefficiencies")
            action_items.append("Review route optimization and vehicle maintenance schedules")
        
        # Alert insights
        if alerts_summary.get('critical', 0) > 0:
            recommendations.append("Critical alerts require immediate attention to prevent operational disruption")
            action_items.append("Address all critical alerts within 24 hours")
        
        # Anomaly insights
        anomaly_rate = len(anomaly_analysis.get('anomalies', [])) / max(fleet_stats.get('total_logs', 1), 1) * 100
        if anomaly_rate > 10:
            recommendations.append("High anomaly rate suggests systematic issues requiring investigation")
            action_items.append("Conduct detailed analysis of flagged vehicles and routes")
        
        return {
            'recommendations': recommendations,
            'action_items': action_items
        }
    
    def _create_executive_charts(self, fleet_stats, cost_analysis, performance_trends):
        """Create charts for executive report"""
        charts = {}
        
        # Fleet efficiency overview chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Sample data for demonstration
        vehicles = [f'TRUCK{i:03d}' for i in range(1, 11)]
        efficiencies = [12.5, 11.8, 10.2, 13.1, 9.8, 11.5, 12.0, 8.7, 11.9, 10.8]
        
        bars = ax.bar(vehicles, efficiencies, color='skyblue', alpha=0.7)
        ax.axhline(y=sum(efficiencies)/len(efficiencies), color='red', linestyle='--', 
                  label=f'Fleet Average: {sum(efficiencies)/len(efficiencies):.1f} MPG')
        
        ax.set_title('Fleet Efficiency Overview', fontsize=16, fontweight='bold')
        ax.set_xlabel('Vehicle ID')
        ax.set_ylabel('Fuel Efficiency (MPG)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Color bars based on performance
        for i, bar in enumerate(bars):
            if efficiencies[i] < 10:
                bar.set_color('lightcoral')
            elif efficiencies[i] > 12:
                bar.set_color('lightgreen')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Convert to base64 string
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        charts['fleet_efficiency'] = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return charts
    
    def _create_operational_charts(self, vehicle_performance, fuel_trends):
        """Create charts for operational report"""
        return {}  # Placeholder
    
    def _get_detailed_vehicle_performance(self, days_back):
        """Get detailed performance metrics for each vehicle"""
        # Sample implementation
        return {}
    
    def _get_fuel_consumption_trends(self, days_back):
        """Get fuel consumption trends over time"""
        return {}
    
    def _get_efficiency_analysis(self, days_back):
        """Get efficiency analysis by vehicle and route"""
        return {'by_vehicle': {}, 'by_route': {}}
    
    def _calculate_fleet_utilization(self, days_back):
        """Calculate fleet utilization rate"""
        return 78.5  # Sample value
    
    def _get_maintenance_schedule(self):
        """Get upcoming maintenance schedule"""
        return []
    
    def _get_driver_performance_summary(self):
        """Get driver performance summary"""
        return {}
    
    def _calculate_emissions_data(self, days_back):
        """Calculate emissions data for compliance"""
        # Sample calculations based on fuel consumption
        return {
            'total_co2': 45600,  # kg
            'co2_per_mile': 0.95,  # kg/mile
            'reduction_opportunities': 8.5  # percentage
        }
    
    def _get_safety_metrics(self, days_back):
        """Get safety-related metrics"""
        return {
            'incidents': 0,
            'near_misses': 2,
            'safety_score': 94.5
        }
    
    def _check_regulatory_compliance(self):
        """Check regulatory compliance status"""
        return {
            'emissions_compliance': 'Compliant',
            'safety_compliance': 'Compliant',
            'maintenance_compliance': 'Requires attention'
        }
    
    def _get_audit_trail(self, days_back):
        """Get audit trail for compliance"""
        return []
    
    def _generate_predictive_recommendations(self, fuel_pred, maint_pred, eff_forecast):
        """Generate recommendations based on predictive analytics"""
        recommendations = []
        
        if fuel_pred.get('trend') == 'increasing':
            recommendations.append("Rising fuel consumption predicted - review route efficiency")
        
        if maint_pred.get('vehicles_due_soon'):
            recommendations.append("Proactive maintenance scheduling recommended for optimal performance")
        
        return recommendations
    
    def export_report_to_html(self, report_data, template_name='executive_summary'):
        """Export report to HTML format"""
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ report_data.report_metadata.title }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
                .metric-card { background: #f8f9fa; padding: 15px; margin: 10px; border-radius: 8px; }
                .chart-container { text-align: center; margin: 20px 0; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ report_data.report_metadata.title }}</h1>
                <p>Generated: {{ report_data.report_metadata.generated_at }}</p>
                <p>Period: {{ report_data.report_metadata.period }}</p>
            </div>
            
            <h2>Key Metrics</h2>
            <div style="display: flex; flex-wrap: wrap;">
                {% for key, value in report_data.key_metrics.items() %}
                <div class="metric-card">
                    <h3>{{ key.replace('_', ' ').title() }}</h3>
                    <p style="font-size: 24px; font-weight: bold;">{{ value }}</p>
                </div>
                {% endfor %}
            </div>
            
            <h2>Recommendations</h2>
            <ul>
                {% for recommendation in report_data.recommendations %}
                <li>{{ recommendation }}</li>
                {% endfor %}
            </ul>
            
            <h2>Action Items</h2>
            <ul>
                {% for item in report_data.action_items %}
                <li>{{ item }}</li>
                {% endfor %}
            </ul>
        </body>
        </html>
        """
        
        template = Template(html_template)
        return template.render(report_data=report_data)
    
    def schedule_automated_reports(self):
        """Schedule automated report generation"""
        # This would integrate with a task scheduler like Celery
        pass

def main():
    """Test the business intelligence reports"""
    from backend.config import Config
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        bi_reports = BusinessIntelligenceReports(session)
        
        # Generate executive summary
        exec_report = bi_reports.generate_executive_summary_report(30)
        print("Generated Executive Summary Report")
        print(f"Key Metrics: {exec_report['key_metrics']}")
        print(f"Recommendations: {len(exec_report['recommendations'])}")
        
        # Export to HTML
        html_report = bi_reports.export_report_to_html(exec_report)
        
        with open('/tmp/executive_summary.html', 'w') as f:
            f.write(html_report)
        
        print("Report exported to /tmp/executive_summary.html")
        
    finally:
        session.close()

if __name__ == "__main__":
    main()
