"""
Real-Time WebSocket Service
Provides real-time updates for FleetFuel360 dashboard
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
import threading
import time
import json
from datetime import datetime
import sys
import os

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.alert_system import AlertSystem
from backend.services.analyze_fuel import FuelAnalysisService

class RealTimeService:
    def __init__(self, app, db_session_factory):
        self.socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
        self.db_session_factory = db_session_factory
        self.active_connections = {}
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # Register WebSocket event handlers
        self.register_handlers()
    
    def register_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            client_id = request.sid
            self.active_connections[client_id] = {
                'connected_at': datetime.now(),
                'subscriptions': []
            }
            
            emit('connection_established', {
                'client_id': client_id,
                'timestamp': datetime.now().isoformat(),
                'message': 'Connected to FleetFuel360 real-time service'
            })
            
            print(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            client_id = request.sid
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            
            print(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
        
        @self.socketio.on('subscribe_alerts')
        def handle_subscribe_alerts(data):
            """Subscribe to real-time alerts"""
            client_id = request.sid
            room = 'alerts'
            
            join_room(room)
            
            if client_id in self.active_connections:
                if 'alerts' not in self.active_connections[client_id]['subscriptions']:
                    self.active_connections[client_id]['subscriptions'].append('alerts')
            
            emit('subscription_confirmed', {
                'service': 'alerts',
                'message': 'Subscribed to real-time alerts'
            })
        
        @self.socketio.on('subscribe_fuel_data')
        def handle_subscribe_fuel_data(data):
            """Subscribe to real-time fuel data updates"""
            client_id = request.sid
            room = 'fuel_data'
            
            join_room(room)
            
            if client_id in self.active_connections:
                if 'fuel_data' not in self.active_connections[client_id]['subscriptions']:
                    self.active_connections[client_id]['subscriptions'].append('fuel_data')
            
            emit('subscription_confirmed', {
                'service': 'fuel_data',
                'message': 'Subscribed to real-time fuel data'
            })
        
        @self.socketio.on('subscribe_vehicle_status')
        def handle_subscribe_vehicle_status(data):
            """Subscribe to vehicle status updates"""
            client_id = request.sid
            vehicle_id = data.get('vehicle_id', 'all')
            room = f'vehicle_{vehicle_id}'
            
            join_room(room)
            
            if client_id in self.active_connections:
                subscription = f'vehicle_{vehicle_id}'
                if subscription not in self.active_connections[client_id]['subscriptions']:
                    self.active_connections[client_id]['subscriptions'].append(subscription)
            
            emit('subscription_confirmed', {
                'service': 'vehicle_status',
                'vehicle_id': vehicle_id,
                'message': f'Subscribed to vehicle {vehicle_id} status updates'
            })
        
        @self.socketio.on('request_dashboard_update')
        def handle_dashboard_update_request():
            """Handle request for dashboard data update"""
            try:
                session = self.db_session_factory()
                
                # Get latest alerts
                alert_system = AlertSystem(session)
                alerts = alert_system.get_active_alerts()
                
                # Get fuel analysis summary
                analysis_service = FuelAnalysisService(session)
                anomalies = analysis_service.detect_anomalies(days_back=7)
                
                session.close()
                
                emit('dashboard_update', {
                    'timestamp': datetime.now().isoformat(),
                    'alerts': alerts[:5],  # Latest 5 alerts
                    'anomaly_count': len(anomalies.get('anomalies', [])),
                    'total_alerts': len(alerts)
                })
                
            except Exception as e:
                emit('error', {
                    'message': f'Failed to get dashboard update: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                })
    
    def start_monitoring(self):
        """Start real-time monitoring thread"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            print("Real-time monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        print("Real-time monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop for real-time updates"""
        last_alert_check = datetime.now()
        last_fuel_check = datetime.now()
        
        while self.monitoring_active:
            try:
                current_time = datetime.now()
                
                # Check for new alerts every 30 seconds
                if (current_time - last_alert_check).seconds >= 30:
                    self._check_and_broadcast_alerts()
                    last_alert_check = current_time
                
                # Check fuel data updates every 60 seconds
                if (current_time - last_fuel_check).seconds >= 60:
                    self._check_and_broadcast_fuel_updates()
                    last_fuel_check = current_time
                
                # Broadcast heartbeat every 5 minutes
                if current_time.minute % 5 == 0 and current_time.second < 5:
                    self._broadcast_heartbeat()
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Wait longer on error
    
    def _check_and_broadcast_alerts(self):
        """Check for new alerts and broadcast to subscribers"""
        try:
            session = self.db_session_factory()
            alert_system = AlertSystem(session)
            
            # Generate new alerts
            new_alerts = alert_system.generate_alerts()
            
            if new_alerts:
                # Broadcast to all clients subscribed to alerts
                self.socketio.emit('new_alerts', {
                    'timestamp': datetime.now().isoformat(),
                    'alerts': new_alerts,
                    'count': len(new_alerts)
                }, room='alerts')
                
                print(f"Broadcasted {len(new_alerts)} new alerts")
            
            session.close()
            
        except Exception as e:
            print(f"Error checking alerts: {e}")
    
    def _check_and_broadcast_fuel_updates(self):
        """Check for fuel data updates and broadcast"""
        try:
            session = self.db_session_factory()
            analysis_service = FuelAnalysisService(session)
            
            # Get recent fuel efficiency data
            recent_data = analysis_service.get_recent_efficiency_data()
            
            if recent_data:
                # Broadcast fuel data update
                self.socketio.emit('fuel_data_update', {
                    'timestamp': datetime.now().isoformat(),
                    'efficiency_data': recent_data,
                    'message': 'Fuel efficiency data updated'
                }, room='fuel_data')
            
            session.close()
            
        except Exception as e:
            print(f"Error checking fuel updates: {e}")
    
    def _broadcast_heartbeat(self):
        """Broadcast heartbeat to all connected clients"""
        heartbeat_data = {
            'timestamp': datetime.now().isoformat(),
            'active_connections': len(self.active_connections),
            'system_status': 'operational',
            'uptime': self._get_uptime()
        }
        
        self.socketio.emit('heartbeat', heartbeat_data)
    
    def _get_uptime(self):
        """Get system uptime in a readable format"""
        # This is a simplified uptime calculation
        return "System operational"
    
    def broadcast_custom_alert(self, alert_data):
        """Broadcast a custom alert to all subscribers"""
        self.socketio.emit('custom_alert', {
            'timestamp': datetime.now().isoformat(),
            'alert': alert_data
        }, room='alerts')
    
    def broadcast_vehicle_update(self, vehicle_id, update_data):
        """Broadcast vehicle-specific update"""
        room = f'vehicle_{vehicle_id}'
        self.socketio.emit('vehicle_update', {
            'timestamp': datetime.now().isoformat(),
            'vehicle_id': vehicle_id,
            'update': update_data
        }, room=room)
        
        # Also broadcast to 'all vehicles' room
        self.socketio.emit('vehicle_update', {
            'timestamp': datetime.now().isoformat(),
            'vehicle_id': vehicle_id,
            'update': update_data
        }, room='vehicle_all')
    
    def get_connection_stats(self):
        """Get real-time connection statistics"""
        return {
            'total_connections': len(self.active_connections),
            'connections': {
                client_id: {
                    'connected_at': conn_data['connected_at'].isoformat(),
                    'subscriptions': conn_data['subscriptions']
                }
                for client_id, conn_data in self.active_connections.items()
            }
        }

# Utility functions for integration
def create_realtime_service(app, db_session_factory):
    """Create and configure real-time service"""
    service = RealTimeService(app, db_session_factory)
    return service

def simulate_real_time_events(realtime_service):
    """Simulate real-time events for demonstration"""
    import random
    
    def simulation_thread():
        while True:
            # Simulate random alerts
            if random.random() < 0.3:  # 30% chance every cycle
                alert_types = ['efficiency_drop', 'fuel_leak', 'maintenance_due']
                severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
                
                simulated_alert = {
                    'vehicle_id': f'TRUCK{random.randint(1, 20):03d}',
                    'type': random.choice(alert_types),
                    'severity': random.choice(severities),
                    'message': 'Simulated alert for demonstration',
                    'timestamp': datetime.now().isoformat()
                }
                
                realtime_service.broadcast_custom_alert(simulated_alert)
            
            # Simulate vehicle updates
            if random.random() < 0.2:  # 20% chance
                vehicle_id = f'TRUCK{random.randint(1, 20):03d}'
                update = {
                    'fuel_level': random.randint(10, 100),
                    'current_efficiency': round(random.uniform(6, 15), 1),
                    'status': random.choice(['Active', 'Idle', 'Maintenance'])
                }
                
                realtime_service.broadcast_vehicle_update(vehicle_id, update)
            
            time.sleep(30)  # Wait 30 seconds between simulations
    
    # Start simulation in a separate thread
    sim_thread = threading.Thread(target=simulation_thread)
    sim_thread.daemon = True
    sim_thread.start()
    
    return sim_thread
