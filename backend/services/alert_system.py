"""
Real-Time Alert System for FleetFuel360
Monitors fuel efficiency and sends instant notifications
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from enum import Enum

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    EFFICIENCY_DROP = "efficiency_drop"
    ANOMALY_DETECTED = "anomaly_detected"
    MAINTENANCE_DUE = "maintenance_due"
    FUEL_LEAK = "fuel_leak"
    EXCESSIVE_IDLING = "excessive_idling"
    ROUTE_INEFFICIENCY = "route_inefficiency"

class Alert:
    def __init__(self, alert_type: AlertType, severity: AlertSeverity, 
                 vehicle_id: str, message: str, data: Dict = None):
        self.id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{vehicle_id}"
        self.alert_type = alert_type
        self.severity = severity
        self.vehicle_id = vehicle_id
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.now()
        self.acknowledged = False
        self.resolved = False

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.alert_type.value,
            'severity': self.severity.value,
            'vehicle_id': self.vehicle_id,
            'message': self.message,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged': self.acknowledged,
            'resolved': self.resolved
        }

class AlertManager:
    def __init__(self):
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.alert_rules = self._load_default_rules()
        
    def _load_default_rules(self):
        """Default alert rules and thresholds"""
        return {
            'efficiency_drop_threshold': 20,  # % drop from baseline
            'anomaly_score_threshold': -0.1,  # Isolation Forest threshold
            'excessive_idling_minutes': 15,   # Minutes of idling
            'fuel_leak_threshold': 5,         # L/100km increase
            'maintenance_km_threshold': 5000  # KM since last maintenance
        }
    
    def check_efficiency_alerts(self, fuel_logs_df, vehicle_specs):
        """Check for fuel efficiency related alerts"""
        alerts = []
        
        for vehicle_id in fuel_logs_df['vehicle_id'].unique():
            vehicle_data = fuel_logs_df[fuel_logs_df['vehicle_id'] == vehicle_id]
            
            if len(vehicle_data) < 2:
                continue
                
            # Calculate recent vs baseline efficiency
            recent_data = vehicle_data.tail(5)  # Last 5 trips
            baseline_data = vehicle_data.head(-5) if len(vehicle_data) > 10 else vehicle_data
            
            recent_efficiency = recent_data['fuel_efficiency'].mean()
            baseline_efficiency = baseline_data['fuel_efficiency'].mean()
            
            if baseline_efficiency > 0:
                efficiency_drop = ((baseline_efficiency - recent_efficiency) / baseline_efficiency) * 100
                
                if efficiency_drop > self.alert_rules['efficiency_drop_threshold']:
                    severity = AlertSeverity.HIGH if efficiency_drop > 30 else AlertSeverity.MEDIUM
                    
                    alert = Alert(
                        alert_type=AlertType.EFFICIENCY_DROP,
                        severity=severity,
                        vehicle_id=vehicle_id,
                        message=f"Fuel efficiency dropped by {efficiency_drop:.1f}% "
                               f"(from {baseline_efficiency:.2f} to {recent_efficiency:.2f} km/L)",
                        data={
                            'efficiency_drop_percent': efficiency_drop,
                            'current_efficiency': recent_efficiency,
                            'baseline_efficiency': baseline_efficiency,
                            'recommendation': self._get_efficiency_recommendation(efficiency_drop)
                        }
                    )
                    alerts.append(alert)
        
        return alerts
    
    def check_anomaly_alerts(self, anomalies_data):
        """Check for ML-detected anomalies"""
        alerts = []
        
        for anomaly in anomalies_data:
            if anomaly.get('anomaly_score', 0) < self.alert_rules['anomaly_score_threshold']:
                severity = AlertSeverity.CRITICAL if anomaly['anomaly_score'] < -0.2 else AlertSeverity.HIGH
                
                alert = Alert(
                    alert_type=AlertType.ANOMALY_DETECTED,
                    severity=severity,
                    vehicle_id=anomaly['vehicle_id'],
                    message=f"Anomalous fuel consumption detected "
                           f"(Score: {anomaly['anomaly_score']:.3f})",
                    data={
                        'anomaly_score': anomaly['anomaly_score'],
                        'fuel_efficiency': anomaly.get('fuel_efficiency'),
                        'timestamp': anomaly.get('timestamp'),
                        'investigation_needed': True
                    }
                )
                alerts.append(alert)
        
        return alerts
    
    def check_maintenance_alerts(self, vehicle_data):
        """Check for maintenance-related alerts"""
        alerts = []
        
        # This would integrate with maintenance tracking system
        # For demo, we'll simulate some maintenance alerts
        for vehicle in vehicle_data:
            # Simulate km since last maintenance
            km_since_maintenance = vehicle.get('km_since_maintenance', 0)
            
            if km_since_maintenance > self.alert_rules['maintenance_km_threshold']:
                alert = Alert(
                    alert_type=AlertType.MAINTENANCE_DUE,
                    severity=AlertSeverity.MEDIUM,
                    vehicle_id=vehicle['vehicle_id'],
                    message=f"Scheduled maintenance overdue by "
                           f"{km_since_maintenance - self.alert_rules['maintenance_km_threshold']} km",
                    data={
                        'km_since_maintenance': km_since_maintenance,
                        'maintenance_type': 'scheduled_service',
                        'urgency': 'medium'
                    }
                )
                alerts.append(alert)
        
        return alerts
    
    def process_new_alerts(self, alerts: List[Alert]):
        """Process and store new alerts"""
        for alert in alerts:
            # Check if similar alert already exists
            if not self._is_duplicate_alert(alert):
                self.active_alerts.append(alert)
                self._send_notification(alert)
    
    def _is_duplicate_alert(self, new_alert: Alert) -> bool:
        """Check if similar alert already exists for the vehicle"""
        for existing_alert in self.active_alerts:
            if (existing_alert.vehicle_id == new_alert.vehicle_id and 
                existing_alert.alert_type == new_alert.alert_type and
                not existing_alert.resolved and
                (datetime.now() - existing_alert.timestamp).hours < 24):
                return True
        return False
    
    def _send_notification(self, alert: Alert):
        """Send notification for new alert"""
        # This would integrate with email, SMS, Slack, etc.
        print(f"🚨 ALERT: {alert.severity.value.upper()} - {alert.message}")
        
        # Log to file for persistence
        self._log_alert(alert)
    
    def _log_alert(self, alert: Alert):
        """Log alert to file"""
        try:
            with open('alerts.log', 'a') as f:
                f.write(f"{alert.timestamp.isoformat()},{alert.severity.value},"
                       f"{alert.vehicle_id},{alert.alert_type.value},"
                       f"\"{alert.message}\"\n")
        except Exception as e:
            print(f"Error logging alert: {e}")
    
    def _get_efficiency_recommendation(self, efficiency_drop):
        """Get recommendation based on efficiency drop"""
        if efficiency_drop > 30:
            return "URGENT: Check engine, tire pressure, and schedule immediate maintenance"
        elif efficiency_drop > 20:
            return "Schedule maintenance check and review driver behavior"
        else:
            return "Monitor closely and consider route optimization"
    
    def get_active_alerts(self, vehicle_id: Optional[str] = None):
        """Get active alerts, optionally filtered by vehicle"""
        alerts = [alert for alert in self.active_alerts if not alert.resolved]
        
        if vehicle_id:
            alerts = [alert for alert in alerts if alert.vehicle_id == vehicle_id]
        
        return sorted(alerts, key=lambda x: (x.severity.value, x.timestamp), reverse=True)
    
    def acknowledge_alert(self, alert_id: str, user_id: str = None):
        """Acknowledge an alert"""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = user_id
                alert.acknowledged_at = datetime.now()
                return True
        return False
    
    def resolve_alert(self, alert_id: str, resolution_note: str = None):
        """Resolve an alert"""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolution_note = resolution_note
                alert.resolved_at = datetime.now()
                self.alert_history.append(alert)
                return True
        return False

class AlertSystem:
    """
    Main alert system for monitoring fleet performance and generating notifications
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.active_alerts = []
        self.alert_history = []
        self.thresholds = {
            'efficiency_drop_percentage': 15.0,  # Alert if efficiency drops by 15%
            'excessive_idle_minutes': 30,        # Alert if idling for 30+ minutes
            'maintenance_due_miles': 1000,       # Alert 1000 miles before maintenance
            'fuel_leak_threshold': 2.0           # Alert if fuel consumption 2x normal
        }
    
    def generate_alerts(self) -> List[Dict]:
        """Generate alerts based on current fleet data"""
        new_alerts = []
        
        try:
            # Import here to avoid circular imports
            from backend.models.vehicle import Vehicle
            from backend.models.fuel_log import FuelLog
            from backend.services.analyze_fuel import FuelAnalysisService
            
            # Get recent fuel logs for analysis
            recent_logs = self.session.query(FuelLog).filter(
                FuelLog.timestamp >= datetime.now() - timedelta(hours=24)
            ).all()
            
            # Analyze each vehicle
            vehicles = self.session.query(Vehicle).all()
            analysis_service = FuelAnalysisService(self.session)
            
            for vehicle in vehicles:
                vehicle_logs = [log for log in recent_logs if log.vehicle_id == vehicle.vehicle_id]
                
                if not vehicle_logs:
                    continue
                
                # Check for efficiency drops
                alerts = self._check_efficiency_drop(vehicle, vehicle_logs)
                new_alerts.extend(alerts)
                
                # Check for anomalies
                anomaly_alerts = self._check_anomalies(vehicle, analysis_service)
                new_alerts.extend(anomaly_alerts)
                
                # Check maintenance due
                maintenance_alerts = self._check_maintenance_due(vehicle)
                new_alerts.extend(maintenance_alerts)
            
            # Store new alerts
            self.active_alerts.extend(new_alerts)
            
            return new_alerts
            
        except Exception as e:
            print(f"Error generating alerts: {e}")
            return []
    
    def get_active_alerts(self, severity=None, alert_type=None, vehicle_id=None) -> List[Dict]:
        """Get currently active alerts with optional filtering"""
        
        # Generate sample alerts for demonstration
        sample_alerts = [
            {
                'id': 'alert_001',
                'vehicle_id': 'TRUCK003',
                'severity': 'HIGH',
                'type': 'efficiency_drop',
                'message': 'Fuel efficiency dropped 18% below average',
                'timestamp': datetime.now().isoformat(),
                'data': {'efficiency_drop': 18.2, 'current_mpg': 8.1, 'average_mpg': 9.9}
            },
            {
                'id': 'alert_002',
                'vehicle_id': 'TRUCK007',
                'severity': 'MEDIUM',
                'type': 'maintenance_due',
                'message': 'Scheduled maintenance due in 800 miles',
                'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
                'data': {'miles_until_maintenance': 800}
            },
            {
                'id': 'alert_003',
                'vehicle_id': 'TRUCK015',
                'severity': 'CRITICAL',
                'type': 'fuel_leak',
                'message': 'Possible fuel leak detected - immediate inspection required',
                'timestamp': (datetime.now() - timedelta(minutes=30)).isoformat(),
                'data': {'fuel_consumption_increase': 45.5}
            }
        ]
        
        filtered_alerts = sample_alerts
        
        # Apply filters
        if severity:
            filtered_alerts = [a for a in filtered_alerts if a['severity'] == severity]
        if alert_type:
            filtered_alerts = [a for a in filtered_alerts if a['type'] == alert_type]
        if vehicle_id:
            filtered_alerts = [a for a in filtered_alerts if a['vehicle_id'] == vehicle_id]
        
        return filtered_alerts
    
    def _check_efficiency_drop(self, vehicle, recent_logs) -> List[Dict]:
        """Check for significant efficiency drops"""
        alerts = []
        
        if len(recent_logs) < 2:
            return alerts
        
        # Calculate recent efficiency
        recent_efficiency = sum(log.km_driven / log.fuel_used for log in recent_logs[-3:]) / min(3, len(recent_logs))
        
        # Compare to vehicle average
        historical_efficiency = vehicle.average_efficiency or 10.0
        
        if historical_efficiency > 0:
            efficiency_drop = ((historical_efficiency - recent_efficiency) / historical_efficiency) * 100
            
            if efficiency_drop > self.thresholds['efficiency_drop_percentage']:
                severity = 'CRITICAL' if efficiency_drop > 25 else 'HIGH'
                alerts.append({
                    'id': f'eff_drop_{vehicle.vehicle_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                    'vehicle_id': vehicle.vehicle_id,
                    'severity': severity,
                    'type': 'efficiency_drop',
                    'message': f'Fuel efficiency dropped {efficiency_drop:.1f}% below average',
                    'timestamp': datetime.now().isoformat(),
                    'data': {
                        'efficiency_drop': efficiency_drop,
                        'current_mpg': recent_efficiency,
                        'average_mpg': historical_efficiency
                    }
                })
        
        return alerts
    
    def _check_anomalies(self, vehicle, analysis_service) -> List[Dict]:
        """Check for anomalies detected by ML model"""
        alerts = []
        
        try:
            # Get recent anomalies for this vehicle
            anomalies = analysis_service.detect_anomalies(days_back=1)
            vehicle_anomalies = [a for a in anomalies.get('anomalies', []) 
                               if a.get('vehicle_id') == vehicle.vehicle_id]
            
            for anomaly in vehicle_anomalies:
                severity = 'HIGH' if anomaly.get('anomaly_score', 0) > 0.8 else 'MEDIUM'
                alerts.append({
                    'id': f'anomaly_{vehicle.vehicle_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                    'vehicle_id': vehicle.vehicle_id,
                    'severity': severity,
                    'type': 'anomaly_detected',
                    'message': f'Anomalous fuel consumption pattern detected',
                    'timestamp': datetime.now().isoformat(),
                    'data': anomaly
                })
        except Exception as e:
            print(f"Error checking anomalies for {vehicle.vehicle_id}: {e}")
        
        return alerts
    
    def _check_maintenance_due(self, vehicle) -> List[Dict]:
        """Check if maintenance is due soon"""
        alerts = []
        
        # Sample maintenance check (in real implementation, this would check actual maintenance schedules)
        import random
        if random.random() < 0.1:  # 10% chance to generate maintenance alert
            miles_until = random.randint(500, 1500)
            severity = 'HIGH' if miles_until < 500 else 'MEDIUM'
            
            alerts.append({
                'id': f'maint_{vehicle.vehicle_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'vehicle_id': vehicle.vehicle_id,
                'severity': severity,
                'type': 'maintenance_due', 
                'message': f'Scheduled maintenance due in {miles_until} miles',
                'timestamp': datetime.now().isoformat(),
                'data': {'miles_until_maintenance': miles_until}
            })
        
        return alerts
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert (mark as seen)"""
        for alert in self.active_alerts:
            if alert.get('id') == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.now().isoformat()
                return True
        return False
    
    def resolve_alert(self, alert_id: str, resolution_notes: str = None) -> bool:
        """Mark an alert as resolved"""
        for i, alert in enumerate(self.active_alerts):
            if alert.get('id') == alert_id:
                alert['status'] = 'resolved'
                alert['resolved_at'] = datetime.now().isoformat()
                alert['resolution_notes'] = resolution_notes
                
                # Move to history
                self.alert_history.append(alert)
                del self.active_alerts[i]
                return True
        return False
    
    def get_alert_statistics(self) -> Dict:
        """Get statistics about alerts"""
        active_by_severity = {}
        active_by_type = {}
        
        for alert in self.active_alerts:
            severity = alert.get('severity', 'UNKNOWN')
            alert_type = alert.get('type', 'UNKNOWN')
            
            active_by_severity[severity] = active_by_severity.get(severity, 0) + 1
            active_by_type[alert_type] = active_by_type.get(alert_type, 0) + 1
        
        return {
            'total_active': len(self.active_alerts),
            'total_resolved': len(self.alert_history),
            'by_severity': active_by_severity,
            'by_type': active_by_type
        }

# Example usage and testing
if __name__ == "__main__":
    import pandas as pd
    
    # Create sample data for testing
    sample_data = {
        'vehicle_id': ['TRUCK001', 'TRUCK001', 'TRUCK002', 'TRUCK002'],
        'fuel_efficiency': [8.0, 6.0, 7.5, 7.2],
        'timestamp': [datetime.now() - timedelta(hours=i) for i in range(4)]
    }
    
    df = pd.DataFrame(sample_data)
    
    # Initialize alert manager
    alert_manager = AlertManager()
    
    # Check for efficiency alerts
    efficiency_alerts = alert_manager.check_efficiency_alerts(df, {})
    
    # Process alerts
    alert_manager.process_new_alerts(efficiency_alerts)
    
    # Get active alerts
    active_alerts = alert_manager.get_active_alerts()
    
    print(f"Generated {len(active_alerts)} alerts:")
    for alert in active_alerts:
        print(f"- {alert.severity.value}: {alert.message}")
