"""
Demo Data Generator
Generates realistic demo data for showcasing FleetFuel360 capabilities
"""

import random
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import numpy as np
import sys
import os

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.vehicle import Vehicle
from backend.models.fuel_log import FuelLog

class DemoDataGenerator:
    def __init__(self, db_session):
        self.session = db_session
        
        # Realistic vehicle types and their characteristics
        self.vehicle_types = {
            'DELIVERY_VAN': {'mpg_base': 18, 'mpg_variance': 3, 'tank_size': 25},
            'SEMI_TRUCK': {'mpg_base': 6.5, 'mpg_variance': 1.5, 'tank_size': 120},
            'PICKUP_TRUCK': {'mpg_base': 22, 'mpg_variance': 4, 'tank_size': 26},
            'BOX_TRUCK': {'mpg_base': 12, 'mpg_variance': 2, 'tank_size': 40},
            'REFRIGERATED_TRUCK': {'mpg_base': 8, 'mpg_variance': 2, 'tank_size': 80}
        }
        
        # Route types and their efficiency impacts
        self.route_types = {
            'CITY_DELIVERY': {'efficiency_modifier': 0.8, 'traffic_factor': 1.3},
            'HIGHWAY_LONG': {'efficiency_modifier': 1.2, 'traffic_factor': 0.9},
            'SUBURBAN': {'efficiency_modifier': 1.0, 'traffic_factor': 1.0},
            'CONSTRUCTION_SITE': {'efficiency_modifier': 0.6, 'traffic_factor': 1.5},
            'EMERGENCY_RESPONSE': {'efficiency_modifier': 0.7, 'traffic_factor': 1.8}
        }
        
        # Driver profiles affecting fuel efficiency
        self.driver_profiles = {
            'EFFICIENT': {'skill_modifier': 1.15, 'consistency': 0.95},
            'AVERAGE': {'skill_modifier': 1.0, 'consistency': 0.85},
            'AGGRESSIVE': {'skill_modifier': 0.85, 'consistency': 0.75},
            'TRAINEE': {'skill_modifier': 0.80, 'consistency': 0.70}
        }
        
        # Weather conditions
        self.weather_conditions = {
            'CLEAR': {'efficiency_modifier': 1.0},
            'RAIN': {'efficiency_modifier': 0.92},
            'SNOW': {'efficiency_modifier': 0.85},
            'WIND': {'efficiency_modifier': 0.88},
            'EXTREME_HEAT': {'efficiency_modifier': 0.90}
        }
    
    def generate_fleet_vehicles(self, count=20):
        """Generate a realistic fleet of vehicles"""
        vehicles = []
        
        for i in range(count):
            vehicle_id = f"TRUCK{i+1:03d}"
            vehicle_type = random.choice(list(self.vehicle_types.keys()))
            type_specs = self.vehicle_types[vehicle_type]
            
            # Generate realistic vehicle data
            vehicle_data = {
                'vehicle_id': vehicle_id,
                'make': random.choice(['Ford', 'Chevrolet', 'Freightliner', 'Peterbilt', 'Volvo', 'Mercedes']),
                'model': f"Model-{random.randint(1000, 9999)}",
                'year': random.randint(2015, 2024),
                'vehicle_type': vehicle_type.replace('_', ' ').title(),
                'fuel_capacity': type_specs['tank_size'],
                'current_mileage': random.randint(50000, 250000)
            }
            
            vehicles.append(vehicle_data)
        
        return vehicles
    
    def generate_realistic_fuel_logs(self, vehicles, days=90):
        """Generate realistic fuel consumption data"""
        fuel_logs = []
        current_date = datetime.now() - timedelta(days=days)
        
        # Track vehicle states
        vehicle_states = {}
        for vehicle in vehicles:
            vehicle_states[vehicle['vehicle_id']] = {
                'current_mileage': vehicle['current_mileage'],
                'driver_profile': random.choice(list(self.driver_profiles.keys())),
                'maintenance_due': random.choice([True, False]) if random.random() < 0.2 else False
            }
        
        for day in range(days):
            date = current_date + timedelta(days=day)
            
            # Skip some vehicles on weekends (realistic operational patterns)
            weekend_skip_probability = 0.6 if date.weekday() >= 5 else 0.1
            
            for vehicle in vehicles:
                if random.random() < weekend_skip_probability:
                    continue
                
                vehicle_id = vehicle['vehicle_id']
                vehicle_type = vehicle['vehicle_type'].upper().replace(' ', '_')
                state = vehicle_states[vehicle_id]
                
                # Determine if vehicle operates today
                if random.random() < 0.85:  # 85% operational probability
                    logs_today = self._generate_daily_logs(
                        vehicle, vehicle_type, state, date
                    )
                    fuel_logs.extend(logs_today)
                    
                    # Update vehicle state
                    if logs_today:
                        total_miles = sum(log['miles_driven'] for log in logs_today)
                        state['current_mileage'] += total_miles
        
        return fuel_logs
    
    def _generate_daily_logs(self, vehicle, vehicle_type, state, date):
        """Generate fuel logs for a single day"""
        logs = []
        vehicle_id = vehicle['vehicle_id']
        
        # Number of fuel-ups per day (varies by vehicle type)
        fuel_ups_today = self._get_daily_fuel_ups(vehicle_type)
        
        for fuel_up in range(fuel_ups_today):
            # Generate route and conditions
            route_type = self._select_route_type(vehicle_type)
            weather = random.choice(list(self.weather_conditions.keys()))
            
            # Calculate realistic miles and fuel consumption
            miles_driven = self._calculate_miles_driven(vehicle_type, route_type)
            fuel_consumed = self._calculate_fuel_consumption(
                vehicle, vehicle_type, route_type, weather, state, miles_driven
            )
            
            # Add some realistic anomalies
            if random.random() < 0.05:  # 5% chance of anomaly
                fuel_consumed *= random.uniform(1.3, 2.0)  # Fuel leak or inefficiency
            
            # Create timestamp for the fuel-up
            timestamp = date + timedelta(
                hours=random.randint(6, 20),
                minutes=random.randint(0, 59)
            )
            
            log = {
                'vehicle_id': vehicle_id,
                'timestamp': timestamp,
                'miles_driven': round(miles_driven, 1),
                'fuel_consumed': round(fuel_consumed, 2),
                'efficiency': round(miles_driven / fuel_consumed if fuel_consumed > 0 else 0, 2),
                'route_type': route_type,
                'weather_condition': weather,
                'driver_profile': state['driver_profile'],
                'location': self._generate_location(),
                'fuel_price': round(random.uniform(3.20, 4.80), 2)
            }
            
            logs.append(log)
        
        return logs
    
    def _get_daily_fuel_ups(self, vehicle_type):
        """Determine how many times a vehicle fuels up per day"""
        fuel_up_patterns = {
            'DELIVERY_VAN': [1, 2],
            'SEMI_TRUCK': [1, 1, 2],  # Weighted toward 1
            'PICKUP_TRUCK': [1],
            'BOX_TRUCK': [1, 2],
            'REFRIGERATED_TRUCK': [1, 2]
        }
        return random.choice(fuel_up_patterns.get(vehicle_type, [1]))
    
    def _select_route_type(self, vehicle_type):
        """Select appropriate route type based on vehicle type"""
        route_preferences = {
            'DELIVERY_VAN': ['CITY_DELIVERY', 'SUBURBAN'],
            'SEMI_TRUCK': ['HIGHWAY_LONG', 'SUBURBAN'],
            'PICKUP_TRUCK': ['SUBURBAN', 'CITY_DELIVERY', 'CONSTRUCTION_SITE'],
            'BOX_TRUCK': ['CITY_DELIVERY', 'SUBURBAN'],
            'REFRIGERATED_TRUCK': ['HIGHWAY_LONG', 'CITY_DELIVERY']
        }
        
        return random.choice(route_preferences.get(vehicle_type, ['SUBURBAN']))
    
    def _calculate_miles_driven(self, vehicle_type, route_type):
        """Calculate realistic miles driven"""
        base_miles = {
            'DELIVERY_VAN': (80, 150),
            'SEMI_TRUCK': (300, 600),
            'PICKUP_TRUCK': (100, 200),
            'BOX_TRUCK': (120, 180),
            'REFRIGERATED_TRUCK': (250, 450)
        }
        
        min_miles, max_miles = base_miles.get(vehicle_type, (100, 200))
        
        # Adjust for route type
        if route_type == 'HIGHWAY_LONG':
            min_miles *= 1.5
            max_miles *= 1.5
        elif route_type == 'CITY_DELIVERY':
            min_miles *= 0.7
            max_miles *= 0.7
        
        return random.uniform(min_miles, max_miles)
    
    def _calculate_fuel_consumption(self, vehicle, vehicle_type, route_type, weather, state, miles_driven):
        """Calculate realistic fuel consumption with various factors"""
        # Base MPG for vehicle type
        type_specs = self.vehicle_types.get(vehicle_type, self.vehicle_types['PICKUP_TRUCK'])
        base_mpg = type_specs['mpg_base']
        variance = type_specs['mpg_variance']
        
        # Apply random variance
        actual_mpg = random.normalvariate(base_mpg, variance)
        
        # Apply modifiers
        route_modifier = self.route_types[route_type]['efficiency_modifier']
        weather_modifier = self.weather_conditions[weather]['efficiency_modifier']
        driver_modifier = self.driver_profiles[state['driver_profile']]['skill_modifier']
        
        # Maintenance impact
        maintenance_modifier = 0.9 if state['maintenance_due'] else 1.0
        
        # Vehicle age impact
        age = 2025 - vehicle['year']
        age_modifier = max(0.85, 1.0 - (age * 0.02))
        
        # Calculate final MPG
        final_mpg = actual_mpg * route_modifier * weather_modifier * driver_modifier * maintenance_modifier * age_modifier
        
        # Ensure minimum MPG
        final_mpg = max(final_mpg, 2.0)
        
        return miles_driven / final_mpg
    
    def _generate_location(self):
        """Generate realistic GPS coordinates"""
        # Sample coordinates around major US cities
        city_centers = [
            {'name': 'New York', 'lat': 40.7128, 'lon': -74.0060},
            {'name': 'Los Angeles', 'lat': 34.0522, 'lon': -118.2437},
            {'name': 'Chicago', 'lat': 41.8781, 'lon': -87.6298},
            {'name': 'Houston', 'lat': 29.7604, 'lon': -95.3698},
            {'name': 'Phoenix', 'lat': 33.4484, 'lon': -112.0740}
        ]
        
        city = random.choice(city_centers)
        
        # Add random offset within ~50 miles
        lat_offset = random.uniform(-0.5, 0.5)
        lon_offset = random.uniform(-0.5, 0.5)
        
        return {
            'latitude': round(city['lat'] + lat_offset, 4),
            'longitude': round(city['lon'] + lon_offset, 4),
            'city': city['name']
        }
    
    def generate_business_scenarios(self):
        """Generate specific business scenarios for demonstration"""
        scenarios = {
            'fuel_leak_detection': {
                'description': 'TRUCK015 showing sudden 40% efficiency drop',
                'vehicle_id': 'TRUCK015',
                'anomaly_type': 'fuel_leak',
                'severity': 'CRITICAL',
                'cost_impact': 1250.00
            },
            'maintenance_prediction': {
                'description': 'TRUCK007 predicted to need maintenance in 3 days',
                'vehicle_id': 'TRUCK007',
                'prediction_type': 'maintenance',
                'days_until': 3,
                'confidence': 0.87
            },
            'route_optimization': {
                'description': 'Route A-12 can save 15% fuel with optimization',
                'route_id': 'A-12',
                'current_efficiency': 8.2,
                'optimized_efficiency': 9.4,
                'potential_savings': 850.00
            },
            'driver_performance': {
                'description': 'Driver training program showing 12% improvement',
                'driver_id': 'D-301',
                'improvement_percentage': 12.5,
                'training_roi': 2.3
            }
        }
        
        return scenarios
    
    def populate_database(self, vehicle_count=20, days=90):
        """Populate database with demo data"""
        try:
            # Generate vehicles
            vehicles = self.generate_fleet_vehicles(vehicle_count)
            
            # Add vehicles to database
            for vehicle_data in vehicles:
                existing = self.session.query(Vehicle).filter_by(
                    vehicle_id=vehicle_data['vehicle_id']
                ).first()
                
                if not existing:
                    vehicle = Vehicle(**vehicle_data)
                    self.session.add(vehicle)
            
            self.session.commit()
            print(f"Added {len(vehicles)} vehicles to database")
            
            # Generate fuel logs
            fuel_logs = self.generate_realistic_fuel_logs(vehicles, days)
            
            # Add fuel logs to database
            added_logs = 0
            for log_data in fuel_logs:
                # Check if log already exists
                existing = self.session.query(FuelLog).filter_by(
                    vehicle_id=log_data['vehicle_id'],
                    timestamp=log_data['timestamp']
                ).first()
                
                if not existing:
                    # Create simplified log for database
                    fuel_log = FuelLog(
                        vehicle_id=log_data['vehicle_id'],
                        timestamp=log_data['timestamp'],
                        miles_driven=log_data['miles_driven'],
                        fuel_consumed=log_data['fuel_consumed'],
                        location=f"{log_data['location']['city']}, {log_data['location']['latitude']}, {log_data['location']['longitude']}"
                    )
                    self.session.add(fuel_log)
                    added_logs += 1
            
            self.session.commit()
            print(f"Added {added_logs} fuel logs to database")
            
            return {
                'vehicles_added': len(vehicles),
                'fuel_logs_added': added_logs,
                'scenarios': self.generate_business_scenarios()
            }
            
        except Exception as e:
            self.session.rollback()
            print(f"Error populating database: {e}")
            raise

def main():
    """Main function for testing the demo data generator"""
    from backend.config import Config
    
    # Create database connection
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        generator = DemoDataGenerator(session)
        result = generator.populate_database(vehicle_count=25, days=60)
        
        print("\n=== Demo Data Generation Complete ===")
        print(f"Vehicles: {result['vehicles_added']}")
        print(f"Fuel Logs: {result['fuel_logs_added']}")
        print("\nBusiness Scenarios Created:")
        for scenario_name, scenario_data in result['scenarios'].items():
            print(f"- {scenario_name}: {scenario_data['description']}")
        
    finally:
        session.close()

if __name__ == "__main__":
    main()
