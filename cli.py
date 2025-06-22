#!/usr/bin/env python3
"""
FleetFuel360 Command Line Interface
Advanced CLI tool for fleet managers and system administrators
"""

import argparse
import json
import sys
import os
from datetime import datetime, timedelta
from tabulate import tabulate
import click
from colorama import init, Fore, Back, Style
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import Config
from backend.services.analyze_fuel import FuelAnalysisService
from backend.services.alert_system import AlertSystem
from backend.services.cost_analysis import CostAnalyzer
from backend.services.demo_data_generator import DemoDataGenerator
from backend.services.bi_reports import BusinessIntelligenceReports

class FleetFuel360CLI:
    def __init__(self):
        self.api_base_url = "http://localhost:5000/api"
        self.config = Config()
        self.db_session = None
        
    def init_database_session(self):
        """Initialize database session"""
        try:
            engine = create_engine(self.config.SQLALCHEMY_DATABASE_URI)
            Session = sessionmaker(bind=engine)
            self.db_session = Session()
            return True
        except Exception as e:
            self.error(f"Failed to connect to database: {e}")
            return False
    
    def close_database_session(self):
        """Close database session"""
        if self.db_session:
            self.db_session.close()
    
    def success(self, message):
        """Print success message"""
        click.echo(f"{Fore.GREEN}✓ {message}")
    
    def error(self, message):
        """Print error message"""
        click.echo(f"{Fore.RED}✗ {message}")
    
    def warning(self, message):
        """Print warning message"""
        click.echo(f"{Fore.YELLOW}⚠ {message}")
    
    def info(self, message):
        """Print info message"""
        click.echo(f"{Fore.BLUE}ℹ {message}")
    
    def header(self, message):
        """Print header message"""
        click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}=== {message} ==={Style.RESET_ALL}")

@click.group()
@click.pass_context
def cli(ctx):
    """FleetFuel360 Command Line Interface - Advanced Fleet Management Tools"""
    ctx.ensure_object(dict)
    ctx.obj['cli'] = FleetFuel360CLI()

@cli.command()
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'csv']), 
              help='Output format')
@click.pass_context
def status(ctx, format):
    """Check system status and health"""
    cli_obj = ctx.obj['cli']
    cli_obj.header("System Status Check")
    
    try:
        # Check API health
        response = requests.get(f"{cli_obj.api_base_url}/health", timeout=5)
        if response.status_code == 200:
            cli_obj.success("API server is running")
            health_data = response.json()
        else:
            cli_obj.error(f"API server returned status {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        cli_obj.error(f"Cannot connect to API server: {e}")
        return
    
    # Check database connection
    if cli_obj.init_database_session():
        cli_obj.success("Database connection established")
        
        # Get system statistics
        try:
            from backend.services.utils import generate_summary_stats
            stats = generate_summary_stats(cli_obj.db_session)
            
            status_data = {
                'API Status': 'Healthy',
                'Database Status': 'Connected',
                'Total Vehicles': stats.get('total_vehicles', 0),
                'Total Fuel Logs': stats.get('total_logs', 0),
                'Average Efficiency': f"{stats.get('average_efficiency', 0):.2f} MPG",
                'Last Updated': health_data.get('timestamp', 'Unknown')
            }
            
            if format == 'json':
                click.echo(json.dumps(status_data, indent=2))
            elif format == 'csv':
                for key, value in status_data.items():
                    click.echo(f"{key},{value}")
            else:
                table_data = [[key, value] for key, value in status_data.items()]
                click.echo(tabulate(table_data, headers=['Metric', 'Value'], tablefmt='grid'))
                
        except Exception as e:
            cli_obj.error(f"Error getting system statistics: {e}")
    else:
        cli_obj.error("Database connection failed")
    
    cli_obj.close_database_session()

@cli.command()
@click.option('--severity', type=click.Choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']), 
              help='Filter by severity level')
@click.option('--vehicle', help='Filter by vehicle ID')
@click.option('--count', default=10, help='Number of alerts to show')
@click.pass_context
def alerts(ctx, severity, vehicle, count):
    """View and manage fleet alerts"""
    cli_obj = ctx.obj['cli']
    cli_obj.header("Fleet Alerts")
    
    if not cli_obj.init_database_session():
        return
    
    try:
        alert_system = AlertSystem(cli_obj.db_session)
        alerts_data = alert_system.get_active_alerts(
            severity=severity, 
            vehicle_id=vehicle
        )
        
        if not alerts_data:
            cli_obj.info("No active alerts found")
            return
        
        # Limit results
        alerts_data = alerts_data[:count]
        
        # Create table
        table_data = []
        for alert in alerts_data:
            table_data.append([
                alert.get('vehicle_id', 'N/A'),
                alert.get('severity', 'N/A'),
                alert.get('type', 'N/A'),
                alert.get('message', 'N/A')[:50] + '...' if len(alert.get('message', '')) > 50 else alert.get('message', 'N/A'),
                alert.get('timestamp', 'N/A')
            ])
        
        headers = ['Vehicle', 'Severity', 'Type', 'Message', 'Timestamp']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
        
        # Show summary
        severity_counts = {}
        for alert in alerts_data:
            sev = alert.get('severity', 'UNKNOWN')
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        cli_obj.info(f"Alert Summary: {severity_counts}")
        
    except Exception as e:
        cli_obj.error(f"Error retrieving alerts: {e}")
    
    cli_obj.close_database_session()

@cli.command()
@click.option('--days', default=30, help='Number of days to analyze')
@click.option('--vehicle', help='Specific vehicle ID to analyze')
@click.pass_context
def analytics(ctx, days, vehicle):
    """Run fuel consumption analytics"""
    cli_obj = ctx.obj['cli']
    cli_obj.header(f"Fuel Analytics - Last {days} Days")
    
    if not cli_obj.init_database_session():
        return
    
    try:
        analysis_service = FuelAnalysisService(cli_obj.db_session)
        
        # Detect anomalies
        anomalies = analysis_service.detect_anomalies(days_back=days)
        
        if anomalies.get('anomalies'):
            cli_obj.warning(f"Found {len(anomalies['anomalies'])} anomalies")
            
            # Show anomaly table
            table_data = []
            for anomaly in anomalies['anomalies'][:10]:  # Show top 10
                table_data.append([
                    anomaly.get('vehicle_id', 'N/A'),
                    f"{anomaly.get('efficiency', 0):.2f}",
                    f"{anomaly.get('anomaly_score', 0):.3f}",
                    anomaly.get('timestamp', 'N/A')[:19]  # Remove microseconds
                ])
            
            headers = ['Vehicle', 'Efficiency (MPG)', 'Anomaly Score', 'Timestamp']
            click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
        else:
            cli_obj.success("No anomalies detected")
        
        # Get model status
        model_status = analysis_service.get_model_status()
        if model_status:
            cli_obj.info(f"ML Model: {model_status.get('model_version', 'Unknown')} "
                        f"- Accuracy: {model_status.get('accuracy', 0):.2%}")
        
    except Exception as e:
        cli_obj.error(f"Error running analytics: {e}")
    
    cli_obj.close_database_session()

@cli.command()
@click.option('--days', default=30, help='Number of days for cost analysis')
@click.option('--export', help='Export to file (specify filename)')
@click.pass_context
def costs(ctx, days, export):
    """Analyze fleet costs and ROI"""
    cli_obj = ctx.obj['cli']
    cli_obj.header(f"Cost Analysis - Last {days} Days")
    
    if not cli_obj.init_database_session():
        return
    
    try:
        cost_service = CostAnalyzer(cli_obj.db_session)
        
        # Get comprehensive cost analysis
        cost_analysis = cost_service.get_comprehensive_cost_analysis(days)
        
        # Get ROI analysis
        roi_analysis = cost_service.calculate_fleet_roi(days)
        
        # Display key metrics
        total_costs = cost_analysis.get('total_costs', {})
        efficiency_metrics = cost_analysis.get('efficiency_metrics', {})
        
        cost_data = {
            'Total Fuel Cost': f"${total_costs.get('fuel_cost', 0):,.2f}",
            'Total Maintenance Cost': f"${total_costs.get('maintenance_cost', 0):,.2f}",
            'Cost per Mile': f"${efficiency_metrics.get('cost_per_mile', 0):.3f}",
            'Cost per Gallon': f"${efficiency_metrics.get('cost_per_gallon', 0):.2f}",
            'Monthly Projection': f"${cost_analysis.get('projections', {}).get('monthly_fuel_cost', 0):,.2f}",
            'Potential Savings': f"${cost_analysis.get('optimization_opportunities', {}).get('potential_monthly_savings', 0):,.2f}"
        }
        
        table_data = [[key, value] for key, value in cost_data.items()]
        click.echo(tabulate(table_data, headers=['Metric', 'Value'], tablefmt='grid'))
        
        # ROI Summary
        if roi_analysis:
            cli_obj.info(f"Fleet ROI: {roi_analysis.get('overall_roi', 0):.1%}")
        
        # Export if requested
        if export:
            export_data = {
                'cost_analysis': cost_analysis,
                'roi_analysis': roi_analysis,
                'generated_at': datetime.now().isoformat()
            }
            
            with open(export, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            cli_obj.success(f"Cost analysis exported to {export}")
        
    except Exception as e:
        cli_obj.error(f"Error analyzing costs: {e}")
    
    cli_obj.close_database_session()

@cli.command()
@click.option('--vehicles', default=20, help='Number of vehicles to generate')
@click.option('--days', default=90, help='Number of days of data to generate')
@click.option('--force', is_flag=True, help='Force regeneration of existing data')
@click.pass_context
def generate_demo_data(ctx, vehicles, days, force):
    """Generate realistic demo data for testing"""
    cli_obj = ctx.obj['cli']
    cli_obj.header("Demo Data Generation")
    
    if not cli_obj.init_database_session():
        return
    
    if not force:
        click.confirm(f'This will generate {vehicles} vehicles with {days} days of data. Continue?', abort=True)
    
    try:
        generator = DemoDataGenerator(cli_obj.db_session)
        
        with click.progressbar(length=100, label='Generating demo data') as bar:
            result = generator.populate_database(vehicles, days)
            bar.update(100)
        
        cli_obj.success(f"Generated {result['vehicles_added']} vehicles")
        cli_obj.success(f"Generated {result['fuel_logs_added']} fuel logs")
        
        # Show business scenarios
        scenarios = result.get('scenarios', {})
        if scenarios:
            cli_obj.info("Business scenarios created:")
            for name, scenario in scenarios.items():
                click.echo(f"  • {scenario['description']}")
        
    except Exception as e:
        cli_obj.error(f"Error generating demo data: {e}")
    
    cli_obj.close_database_session()

@cli.command()
@click.option('--type', default='executive', 
              type=click.Choice(['executive', 'operational', 'compliance', 'predictive']),
              help='Type of report to generate')
@click.option('--days', default=30, help='Number of days to include in report')
@click.option('--output', default='report.html', help='Output filename')
@click.pass_context
def report(ctx, type, days, output):
    """Generate business intelligence reports"""
    cli_obj = ctx.obj['cli']
    cli_obj.header(f"Generating {type.title()} Report")
    
    if not cli_obj.init_database_session():
        return
    
    try:
        bi_reports = BusinessIntelligenceReports(cli_obj.db_session)
        
        with click.progressbar(label='Generating report') as bar:
            if type == 'executive':
                report_data = bi_reports.generate_executive_summary_report(days)
                bar.update(25)
            elif type == 'operational':
                report_data = bi_reports.generate_operational_report(days)
                bar.update(25)
            elif type == 'compliance':
                report_data = bi_reports.generate_compliance_report(days)
                bar.update(25)
            elif type == 'predictive':
                report_data = bi_reports.generate_predictive_report()
                bar.update(25)
            
            bar.update(50)
            
            # Export to HTML
            html_content = bi_reports.export_report_to_html(report_data, type)
            bar.update(75)
            
            with open(output, 'w') as f:
                f.write(html_content)
            bar.update(100)
        
        cli_obj.success(f"Report generated: {output}")
        
        # Show key metrics
        if 'key_metrics' in report_data:
            metrics = report_data['key_metrics']
            cli_obj.info("Key Metrics:")
            for key, value in metrics.items():
                click.echo(f"  • {key.replace('_', ' ').title()}: {value}")
        
    except Exception as e:
        cli_obj.error(f"Error generating report: {e}")
    
    cli_obj.close_database_session()

@cli.command()
@click.option('--vehicle', help='Monitor specific vehicle')
@click.option('--interval', default=30, help='Update interval in seconds')
@click.pass_context
def monitor(ctx, vehicle, interval):
    """Real-time fleet monitoring"""
    cli_obj = ctx.obj['cli']
    cli_obj.header("Real-Time Fleet Monitoring")
    
    if not cli_obj.init_database_session():
        return
    
    try:
        import time
        
        cli_obj.info(f"Monitoring every {interval} seconds. Press Ctrl+C to stop.")
        
        while True:
            # Clear screen
            click.clear()
            cli_obj.header(f"Fleet Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Get current alerts
            alert_system = AlertSystem(cli_obj.db_session)
            recent_alerts = alert_system.get_active_alerts()
            
            if recent_alerts:
                click.echo(f"{Fore.RED}🚨 {len(recent_alerts)} Active Alerts")
                for alert in recent_alerts[:5]:  # Show top 5
                    severity_color = {
                        'CRITICAL': Fore.RED,
                        'HIGH': Fore.YELLOW,
                        'MEDIUM': Fore.BLUE,
                        'LOW': Fore.GREEN
                    }.get(alert.get('severity', ''), Fore.WHITE)
                    
                    click.echo(f"{severity_color}  • {alert.get('vehicle_id', 'N/A')}: {alert.get('message', 'N/A')}")
            else:
                click.echo(f"{Fore.GREEN}✓ No active alerts")
            
            # Get fleet statistics
            from backend.services.utils import generate_summary_stats
            stats = generate_summary_stats(cli_obj.db_session, days_back=1)
            
            click.echo(f"\n{Fore.CYAN}Fleet Status:")
            click.echo(f"  • Active Vehicles: {stats.get('total_vehicles', 0)}")
            click.echo(f"  • Average Efficiency: {stats.get('average_efficiency', 0):.2f} MPG")
            click.echo(f"  • Total Miles Today: {stats.get('total_miles', 0):.1f}")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        cli_obj.info("Monitoring stopped")
    except Exception as e:
        cli_obj.error(f"Monitoring error: {e}")
    
    cli_obj.close_database_session()

@cli.command()
@click.pass_context
def dashboard(ctx):
    """Open web dashboard in browser"""
    cli_obj = ctx.obj['cli']
    
    try:
        import webbrowser
        url = "http://localhost:5000"
        
        # Check if server is running
        response = requests.get(f"{url}/api/health", timeout=5)
        if response.status_code == 200:
            webbrowser.open(url)
            cli_obj.success(f"Opening dashboard at {url}")
        else:
            cli_obj.error("Dashboard server is not running")
            cli_obj.info("Start the server with: python app.py")
    except requests.exceptions.RequestException:
        cli_obj.error("Cannot connect to dashboard server")
        cli_obj.info("Start the server with: python app.py")
    except Exception as e:
        cli_obj.error(f"Error opening dashboard: {e}")

if __name__ == '__main__':
    # Make sure required packages are available
    try:
        import tabulate, click, colorama, requests
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Install with: pip install tabulate click colorama requests")
        sys.exit(1)
    
    cli()
