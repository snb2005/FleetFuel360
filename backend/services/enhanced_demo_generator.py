"""
Enhanced Demo Data Generator
Creates realistic, comprehensive dataset for ML training and feature demonstration
"""

import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import sys
import os

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.vehicle import Vehicle
from backend.models.fuel_log import FuelLog

class EnhancedDemoDataGenerator:
    def __init__(self, db_session):
        self.session = db_session
        
        # Enhanced vehicle fleet with realistic characteristics
        self.vehicle_fleet = {
            'delivery_vans': {
                'count': 8,
                'mpg_range': (16, 22),
                'tank_size': 25,
                'daily_miles': (80, 150),
                'fuel_ups_per_day': [1, 2],
                'routes': ['CITY_DELIVERY', 'SUBURBAN']
            },
            'semi_trucks': {
                'count': 6,
                'mpg_range': (5.5, 8.5),
                'tank_size': 120,
                'daily_miles': (300, 600),
                'fuel_ups_per_day': [1, 1, 2],
                'routes': ['HIGHWAY_LONG', 'INTERSTATE']
            },
            'pickup_trucks': {
                'count': 5,
                'mpg_range': (18, 26),
                'tank_size': 26,
                'daily_miles': (100, 250),
                'fuel_ups_per_day': [1, 2],
                'routes': ['SUBURBAN', 'CONSTRUCTION_SITE', 'CITY_DELIVERY']
            },
            'box_trucks': {
                'count': 4,
                'mpg_range': (10, 14),
                'tank_size': 40,
                'daily_miles': (120, 200),
                'fuel_ups_per_day': [1, 2],
                'routes': ['CITY_DELIVERY', 'SUBURBAN']
            },
            'emergency_vehicles': {
                'count': 2,
                'mpg_range': (8, 12),
                'tank_size': 30,
                'daily_miles': (150, 300),
                'fuel_ups_per_day': [2, 3],
                'routes': ['EMERGENCY_RESPONSE', 'CITY_DELIVERY']
            }
        }
        
        # Enhanced route characteristics
        self.routes = {
            'CITY_DELIVERY': {
                'efficiency_modifier': 0.75,
                'traffic_factor': 1.4,
                'stop_frequency': 'high',
                'idling_time': 25,  # minutes per day
                'avg_speed': 25
            },
            'HIGHWAY_LONG': {
                'efficiency_modifier': 1.25,
                'traffic_factor': 0.9,
                'stop_frequency': 'low',
                'idling_time': 5,
                'avg_speed': 65
            },
            'SUBURBAN': {
                'efficiency_modifier': 1.0,
                'traffic_factor': 1.1,
                'stop_frequency': 'medium',
                'idling_time': 15,
                'avg_speed': 35
            },
            'CONSTRUCTION_SITE': {
                'efficiency_modifier': 0.6,
                'traffic_factor': 1.6,
                'stop_frequency': 'very_high',
                'idling_time': 45,
                'avg_speed': 15
            },
            'EMERGENCY_RESPONSE': {
                'efficiency_modifier': 0.7,
                'traffic_factor': 1.8,
                'stop_frequency': 'variable',
                'idling_time': 20,
                'avg_speed': 40
            },
            'INTERSTATE': {
                'efficiency_modifier': 1.3,
                'traffic_factor': 0.85,
                'stop_frequency': 'very_low',
                'idling_time': 3,
                'avg_speed': 70
            }
        }
        
        # Driver profiles with realistic characteristics
        self.driver_profiles = {
            'EFFICIENT': {
                'skill_modifier': 1.18,
                'consistency': 0.95,
                'acceleration_style': 'smooth',
                'braking_style': 'gradual',
                'speed_adherence': 0.98
            },
            'EXPERIENCED': {
                'skill_modifier': 1.12,
                'consistency': 0.92,
                'acceleration_style': 'moderate',
                'braking_style': 'moderate',
                'speed_adherence': 0.95
            },
            'AVERAGE': {
                'skill_modifier': 1.0,
                'consistency': 0.85,
                'acceleration_style': 'moderate',
                'braking_style': 'moderate',
                'speed_adherence': 0.90
            },
            'AGGRESSIVE': {
                'skill_modifier': 0.82,
                'consistency': 0.75,
                'acceleration_style': 'fast',
                'braking_style': 'hard',
                'speed_adherence': 0.85
            },
            'TRAINEE': {
                'skill_modifier': 0.78,
                'consistency': 0.65,
                'acceleration_style': 'variable',
                'braking_style': 'variable',
                'speed_adherence': 0.92
            }
        }
        
        # Weather conditions and their effects
        self.weather_conditions = {
            'CLEAR': {'efficiency_modifier': 1.0, 'frequency': 0.40},
            'PARTLY_CLOUDY': {'efficiency_modifier': 0.98, 'frequency': 0.25},
            'RAIN': {'efficiency_modifier': 0.92, 'frequency': 0.15},
            'HEAVY_RAIN': {'efficiency_modifier': 0.85, 'frequency': 0.05},
            'SNOW': {'efficiency_modifier': 0.80, 'frequency': 0.08},
            'WIND': {'efficiency_modifier': 0.88, 'frequency': 0.05},
            'FOG': {'efficiency_modifier': 0.90, 'frequency': 0.02}
        }
        
        # Seasonal factors
        self.seasonal_factors = {
            'winter': {'months': [12, 1, 2], 'efficiency_modifier': 0.88, 'ac_usage': 0.1},
            'spring': {'months': [3, 4, 5], 'efficiency_modifier': 1.05, 'ac_usage': 0.2},
            'summer': {'months': [6, 7, 8], 'efficiency_modifier': 0.92, 'ac_usage': 0.8},
            'fall': {'months': [9, 10, 11], 'efficiency_modifier': 1.02, 'ac_usage': 0.3}
        }
    
    def generate_enhanced_fleet(self):
        """Generate enhanced fleet with realistic vehicle specifications"""
        vehicles = []
        vehicle_id_counter = 1
        
        for vehicle_type, specs in self.vehicle_fleet.items():
            for i in range(specs['count']):
                vehicle_id = f"TRUCK{vehicle_id_counter:03d}"
                
                # Generate realistic vehicle data
                vehicle = {
                    'vehicle_id': vehicle_id,
                    'make': self._get_realistic_make(vehicle_type),
                    'model': self._get_realistic_model(vehicle_type),
                    'year': random.randint(2018, 2024),
                    'fuel_capacity': specs['tank_size'],
                    'vehicle_type': vehicle_type  # Keep this for fuel log generation
                }
                
                vehicles.append(vehicle)
                vehicle_id_counter += 1
        
        return vehicles
    
    def _get_realistic_make(self, vehicle_type):
        """Get realistic vehicle make based on type"""
        makes = {
            'delivery_vans': ['Ford', 'Mercedes', 'Ram', 'Chevrolet'],
            'semi_trucks': ['Freightliner', 'Peterbilt', 'Kenworth', 'Volvo', 'Mack'],
            'pickup_trucks': ['Ford', 'Chevrolet', 'Ram', 'GMC', 'Toyota'],
            'box_trucks': ['Isuzu', 'Ford', 'Chevrolet', 'Mercedes'],
            'emergency_vehicles': ['Ford', 'Chevrolet', 'Dodge']
        }
        return random.choice(makes.get(vehicle_type, ['Ford', 'Chevrolet']))
    
    def _get_realistic_model(self, vehicle_type):
        """Get realistic vehicle model based on type"""
        models = {
            'delivery_vans': ['Transit', 'Sprinter', 'ProMaster', 'Express'],
            'semi_trucks': ['Cascadia', '579', 'T680', 'VNL', 'Anthem'],
            'pickup_trucks': ['F-150', 'Silverado', '1500', 'Sierra', 'Tacoma'],
            'box_trucks': ['NPR', 'E-Series', '4500', 'Sprinter'],
            'emergency_vehicles': ['F-450', 'Silverado 3500', 'Ram 3500']
        }
        return random.choice(models.get(vehicle_type, ['Model-' + str(random.randint(1000, 9999))]))
    
    def generate_comprehensive_fuel_logs(self, vehicles, days=120):
        """Generate comprehensive fuel consumption data with realistic patterns"""
        fuel_logs = []
        current_date = datetime.now() - timedelta(days=days)
        
        # Track vehicle states
        vehicle_states = {}
        for vehicle in vehicles:
            vehicle_type = vehicle['vehicle_type'].lower().replace(' ', '_')
            
            vehicle_states[vehicle['vehicle_id']] = {
                'current_mileage': random.randint(20000, 180000),  # Track separately for realistic data
                'driver_profile': random.choice(list(self.driver_profiles.keys())),
                'maintenance_due': random.choice([True, False]) if random.random() < 0.15 else False,
                'vehicle_type': vehicle_type,
                'base_efficiency': self._get_base_efficiency(vehicle_type),
                'fuel_tank_size': vehicle['fuel_capacity'],
                'last_maintenance': current_date - timedelta(days=random.randint(10, 90))
            }
        
        # Generate daily logs
        for day in range(days):
            date = current_date + timedelta(days=day)
            day_of_week = date.weekday()
            
            # Weekend operation probability (reduced for most vehicle types)
            weekend_operation_prob = 0.3 if day_of_week >= 5 else 0.92
            
            # Seasonal adjustments
            season = self._get_season(date.month)
            seasonal_modifier = self.seasonal_factors[season]['efficiency_modifier']
            
            for vehicle in vehicles:
                vehicle_id = vehicle['vehicle_id']
                state = vehicle_states[vehicle_id]
                
                # Determine if vehicle operates today
                if random.random() < weekend_operation_prob:
                    # Generate weather for the day
                    weather = self._generate_weather(season)
                    
                    # Generate logs for this vehicle today
                    daily_logs = self._generate_vehicle_daily_logs(
                        vehicle, state, date, weather, seasonal_modifier
                    )
                    
                    fuel_logs.extend(daily_logs)
                    
                    # Update vehicle state
                    if daily_logs:
                        total_miles = sum(log['miles_driven'] for log in daily_logs)
                        state['current_mileage'] += total_miles
                        
                        # Check for maintenance
                        days_since_maintenance = (date - state['last_maintenance']).days
                        if days_since_maintenance > 60:
                            state['maintenance_due'] = True
        
        return fuel_logs
    
    def _get_base_efficiency(self, vehicle_type):
        """Get base fuel efficiency for vehicle type"""
        for fleet_type, specs in self.vehicle_fleet.items():
            if fleet_type == vehicle_type:
                return random.uniform(*specs['mpg_range'])
        return 12.0  # Default
    
    def _get_season(self, month):
        """Get season based on month"""
        for season, data in self.seasonal_factors.items():
            if month in data['months']:
                return season
        return 'spring'
    
    def _generate_weather(self, season):
        """Generate weather based on season and probabilities"""
        weights = []
        conditions = []
        
        for condition, data in self.weather_conditions.items():
            # Adjust frequency based on season
            frequency = data['frequency']
            if season == 'winter' and condition in ['SNOW', 'RAIN']:
                frequency *= 2
            elif season == 'summer' and condition == 'CLEAR':
                frequency *= 1.2
            
            weights.append(frequency)
            conditions.append(condition)
        
        return random.choices(conditions, weights=weights)[0]
    
    def _generate_vehicle_daily_logs(self, vehicle, state, date, weather, seasonal_modifier):
        """Generate fuel logs for a single vehicle for one day"""
        logs = []
        vehicle_type = state['vehicle_type']
        
        # Get vehicle type specifications
        specs = None
        for fleet_type, fleet_specs in self.vehicle_fleet.items():
            if fleet_type == vehicle_type:
                specs = fleet_specs
                break
        
        if not specs:
            return logs
        
        # Number of fuel-ups today
        fuel_ups_today = random.choice(specs['fuel_ups_per_day'])
        
        # Split daily activity into fuel-up sessions
        total_daily_miles = random.uniform(*specs['daily_miles'])
        miles_per_session = total_daily_miles / fuel_ups_today
        
        for session in range(fuel_ups_today):
            # Generate session details
            route_type = random.choice(specs['routes'])
            miles_driven = miles_per_session + random.uniform(-20, 20)
            miles_driven = max(10, miles_driven)  # Minimum miles
            
            # Calculate fuel consumption with all factors
            fuel_consumed = self._calculate_enhanced_fuel_consumption(
                vehicle, state, route_type, weather, seasonal_modifier, miles_driven, date
            )
            
            # Add realistic anomalies (mechanical issues, fuel leaks, etc.)
            anomaly_factor = self._generate_anomaly_factor(vehicle, state, date)
            fuel_consumed *= anomaly_factor
            
            # Create timestamp for fuel-up
            base_hour = 6 + (session * 8)  # Spread throughout work day
            timestamp = date + timedelta(
                hours=base_hour + random.randint(-1, 3),
                minutes=random.randint(0, 59)
            )
            
            # Calculate efficiency
            efficiency = miles_driven / fuel_consumed if fuel_consumed > 0 else 0
            
            log = {
                'vehicle_id': vehicle['vehicle_id'],
                'timestamp': timestamp,
                'miles_driven': round(miles_driven, 1),
                'fuel_consumed': round(fuel_consumed, 2),
                'efficiency': round(efficiency, 2),
                'route_type': route_type,
                'weather_condition': weather,
                'driver_profile': state['driver_profile'],
                'location': self._generate_realistic_location(route_type),
                'fuel_price': self._generate_realistic_fuel_price(date),
                'maintenance_due': state['maintenance_due'],
                'seasonal_factor': seasonal_modifier,
                'anomaly_factor': anomaly_factor
            }
            
            logs.append(log)
        
        return logs
    
    def _calculate_enhanced_fuel_consumption(self, vehicle, state, route_type, weather, seasonal_modifier, miles_driven, date):
        """Calculate fuel consumption with comprehensive factors"""
        
        # Base efficiency
        base_mpg = state['base_efficiency']
        
        # Route impact
        route_modifier = self.routes[route_type]['efficiency_modifier']
        traffic_modifier = 1 / self.routes[route_type]['traffic_factor']
        
        # Weather impact
        weather_modifier = self.weather_conditions[weather]['efficiency_modifier']
        
        # Driver impact
        driver_modifier = self.driver_profiles[state['driver_profile']]['skill_modifier']
        
        # Maintenance impact
        maintenance_modifier = 0.88 if state['maintenance_due'] else 1.0
        
        # Vehicle age impact
        vehicle_age = 2025 - vehicle['year']
        age_modifier = max(0.82, 1.0 - (vehicle_age * 0.025))
        
        # Time of day impact (traffic patterns)
        hour = date.hour if hasattr(date, 'hour') else 12
        time_modifier = self._get_time_of_day_modifier(hour, route_type)
        
        # Load factor (vehicle utilization)
        load_modifier = random.uniform(0.92, 1.08)  # ±8% based on load
        
        # Calculate final MPG
        final_mpg = (base_mpg * 
                    route_modifier * 
                    traffic_modifier * 
                    weather_modifier * 
                    driver_modifier * 
                    maintenance_modifier * 
                    age_modifier * 
                    seasonal_modifier * 
                    time_modifier * 
                    load_modifier)
        
        # Ensure minimum reasonable MPG
        final_mpg = max(final_mpg, 3.0)
        
        return miles_driven / final_mpg
    
    def _get_time_of_day_modifier(self, hour, route_type):
        """Get efficiency modifier based on time of day and route"""
        if route_type in ['CITY_DELIVERY', 'SUBURBAN']:
            # Rush hour penalties
            if 7 <= hour <= 9 or 16 <= hour <= 18:
                return 0.85  # Heavy traffic
            elif 10 <= hour <= 15:
                return 1.05  # Light traffic
        elif route_type == 'HIGHWAY_LONG':
            # Night driving bonus
            if 22 <= hour or hour <= 5:
                return 1.1  # Less traffic
        
        return 1.0  # Normal conditions
    
    def _generate_anomaly_factor(self, vehicle, state, date):
        """Generate anomaly factors for realistic mechanical issues"""
        
        # Higher chance of issues with older vehicles
        vehicle_age = 2025 - vehicle['year']
        age_anomaly_prob = vehicle_age * 0.008
        
        # Maintenance overdue increases anomaly chance
        maintenance_anomaly_prob = 0.02 if state['maintenance_due'] else 0.005
        
        # Random mechanical issues
        total_anomaly_prob = age_anomaly_prob + maintenance_anomaly_prob
        
        if random.random() < total_anomaly_prob:
            # Generate different types of anomalies
            anomaly_types = {
                'fuel_leak': random.uniform(1.3, 2.5),      # 30-150% increase
                'engine_issue': random.uniform(1.2, 1.8),   # 20-80% increase  
                'tire_pressure': random.uniform(1.1, 1.3),  # 10-30% increase
                'air_filter': random.uniform(1.05, 1.25),   # 5-25% increase
                'transmission': random.uniform(1.15, 1.6)   # 15-60% increase
            }
            
            return random.choice(list(anomaly_types.values()))
        
        # Normal operation with small variations
        return random.uniform(0.95, 1.05)
    
    def _generate_realistic_location(self, route_type):
        """Generate realistic GPS coordinates based on route type"""
        
        # Base locations for different route types
        base_locations = {
            'CITY_DELIVERY': [
                {'name': 'Downtown', 'lat': 40.7589, 'lon': -73.9851},
                {'name': 'Midtown', 'lat': 40.7505, 'lon': -73.9934},
                {'name': 'Financial District', 'lat': 40.7074, 'lon': -74.0113}
            ],
            'HIGHWAY_LONG': [
                {'name': 'I-95 Corridor', 'lat': 39.7392, 'lon': -75.5402},
                {'name': 'I-80 Route', 'lat': 40.9176, 'lon': -74.1718},
                {'name': 'I-287 Loop', 'lat': 40.8607, 'lon': -74.2735}
            ],
            'SUBURBAN': [
                {'name': 'Westchester', 'lat': 41.1220, 'lon': -73.7949},
                {'name': 'Nassau County', 'lat': 40.6546, 'lon': -73.5594},
                {'name': 'Bergen County', 'lat': 40.9265, 'lon': -74.0753}
            ],
            'CONSTRUCTION_SITE': [
                {'name': 'Site Alpha', 'lat': 40.6892, 'lon': -74.0445},
                {'name': 'Site Beta', 'lat': 40.8176, 'lon': -73.9442},
                {'name': 'Site Gamma', 'lat': 40.7831, 'lon': -73.9712}
            ],
            'EMERGENCY_RESPONSE': [
                {'name': 'Station 1', 'lat': 40.7282, 'lon': -73.7949},
                {'name': 'Station 2', 'lat': 40.7589, 'lon': -73.9851},
                {'name': 'Station 3', 'lat': 40.6892, 'lon': -74.0445}
            ]
        }
        
        base_location = random.choice(base_locations.get(route_type, base_locations['SUBURBAN']))
        
        # Add realistic variance (within 10-mile radius)
        lat_variance = random.uniform(-0.15, 0.15)
        lon_variance = random.uniform(-0.15, 0.15)
        
        return {
            'latitude': round(base_location['lat'] + lat_variance, 4),
            'longitude': round(base_location['lon'] + lon_variance, 4),
            'location_name': base_location['name']
        }
    
    def _generate_realistic_fuel_price(self, date):
        """Generate realistic fuel price with temporal variations"""
        
        # Base price with seasonal variations
        base_price = 3.85
        
        # Seasonal price adjustments
        month = date.month
        if month in [6, 7, 8]:  # Summer driving season
            seasonal_adjustment = 0.15
        elif month in [12, 1, 2]:  # Winter blend
            seasonal_adjustment = 0.08
        else:
            seasonal_adjustment = 0.0
        
        # Weekly price volatility
        weekly_variance = random.uniform(-0.12, 0.12)
        
        # Daily small variations
        daily_variance = random.uniform(-0.05, 0.05)
        
        final_price = base_price + seasonal_adjustment + weekly_variance + daily_variance
        return round(max(final_price, 3.20), 2)  # Minimum $3.20
    
    def populate_enhanced_database(self, days=120):
        """Populate database with enhanced realistic data"""
        try:
            print("🚀 Generating enhanced fleet data...")
            
            # Generate vehicles
            vehicles = self.generate_enhanced_fleet()
            
            # Add vehicles to database
            added_vehicles = 0
            for vehicle_data in vehicles:
                existing = self.session.query(Vehicle).filter_by(
                    vehicle_id=vehicle_data['vehicle_id']
                ).first()
                
                if not existing:
                    # Create vehicle with only valid database fields
                    db_vehicle_data = {
                        'vehicle_id': vehicle_data['vehicle_id'],
                        'make': vehicle_data['make'],
                        'model': vehicle_data['model'],
                        'year': vehicle_data['year'],
                        'fuel_capacity': vehicle_data['fuel_capacity']
                    }
                    vehicle = Vehicle(**db_vehicle_data)
                    self.session.add(vehicle)
                    added_vehicles += 1
            
            self.session.commit()
            print(f"✅ Added {added_vehicles} vehicles to database")
            
            # Generate comprehensive fuel logs
            print("🔄 Generating comprehensive fuel consumption data...")
            fuel_logs = self.generate_comprehensive_fuel_logs(vehicles, days)
            
            # Add fuel logs to database
            added_logs = 0
            for log_data in fuel_logs:
                existing = self.session.query(FuelLog).filter_by(
                    vehicle_id=log_data['vehicle_id'],
                    timestamp=log_data['timestamp']
                ).first()
                
                if not existing:
                    # Create database-compatible fuel log
                    # Convert miles to kilometers (1 mile = 1.60934 km)
                    km_driven = log_data['miles_driven'] * 1.60934
                    fuel_used_liters = log_data['fuel_consumed'] * 3.78541  # Convert gallons to liters
                    
                    fuel_log = FuelLog(
                        vehicle_id=log_data['vehicle_id'],
                        timestamp=log_data['timestamp'],
                        km_driven=round(km_driven, 2),
                        fuel_used=round(fuel_used_liters, 2),
                        # fuel_efficiency is a generated column, don't set it
                        is_anomaly=log_data.get('anomaly_factor', 1.0) > 1.2,
                        anomaly_score=log_data.get('anomaly_factor', 1.0) - 1.0
                    )
                    self.session.add(fuel_log)
                    added_logs += 1
                    
                    # Commit in batches for performance
                    if added_logs % 100 == 0:
                        self.session.commit()
            
            self.session.commit()
            print(f"✅ Added {added_logs} fuel logs to database")
            
            # Generate enhanced analytics summary
            return self._generate_dataset_summary(vehicles, fuel_logs)
            
        except Exception as e:
            self.session.rollback()
            print(f"❌ Error populating enhanced database: {e}")
            raise
    
    def _generate_dataset_summary(self, vehicles, fuel_logs):
        """Generate comprehensive summary of generated dataset"""
        
        # Vehicle type distribution
        vehicle_types = {}
        for vehicle in vehicles:
            vtype = vehicle['vehicle_type']
            vehicle_types[vtype] = vehicle_types.get(vtype, 0) + 1
        
        # Efficiency statistics
        efficiencies = [log['efficiency'] for log in fuel_logs if log['efficiency'] > 0]
        
        # Anomaly detection potential
        anomalies = [log for log in fuel_logs if log.get('anomaly_factor', 1.0) > 1.2]
        
        summary = {
            'vehicles_generated': len(vehicles),
            'fuel_logs_generated': len(fuel_logs),
            'vehicle_type_distribution': vehicle_types,
            'efficiency_stats': {
                'min_mpg': min(efficiencies) if efficiencies else 0,
                'max_mpg': max(efficiencies) if efficiencies else 0,
                'avg_mpg': sum(efficiencies) / len(efficiencies) if efficiencies else 0,
                'total_miles': sum(log['miles_driven'] for log in fuel_logs),
                'total_fuel': sum(log['fuel_consumed'] for log in fuel_logs)
            },
            'anomaly_potential': {
                'total_anomalies': len(anomalies),
                'anomaly_rate': len(anomalies) / len(fuel_logs) * 100 if fuel_logs else 0
            },
            'data_quality': {
                'date_range_days': 120,
                'avg_logs_per_vehicle': len(fuel_logs) / len(vehicles) if vehicles else 0,
                'weather_conditions': len(set(log['weather_condition'] for log in fuel_logs)),
                'route_types': len(set(log['route_type'] for log in fuel_logs))
            }
        }
        
        return summary

def main():
    """Main function for enhanced demo data generation"""
    from backend.config import Config
    
    # Create database connection
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        generator = EnhancedDemoDataGenerator(session)
        result = generator.populate_enhanced_database(days=120)
        
        print("\n" + "="*60)
        print("🎯 ENHANCED DATASET GENERATION COMPLETE")
        print("="*60)
        print(f"📊 Vehicles Generated: {result['vehicles_generated']}")
        print(f"📈 Fuel Logs Generated: {result['fuel_logs_generated']:,}")
        print(f"📅 Date Range: {result['data_quality']['date_range_days']} days")
        print(f"⛽ Total Fuel Consumed: {result['efficiency_stats']['total_fuel']:,.1f} gallons")
        print(f"🛣️  Total Miles Driven: {result['efficiency_stats']['total_miles']:,.1f} miles")
        print(f"📊 Average Fleet MPG: {result['efficiency_stats']['avg_mpg']:.2f}")
        print(f"🚨 Anomalies for ML Training: {result['anomaly_potential']['total_anomalies']} ({result['anomaly_potential']['anomaly_rate']:.1f}%)")
        
        print(f"\n🚛 Vehicle Fleet Composition:")
        for vtype, count in result['vehicle_type_distribution'].items():
            print(f"   • {vtype}: {count} vehicles")
        
        print(f"\n📊 Data Quality Metrics:")
        print(f"   • Avg logs per vehicle: {result['data_quality']['avg_logs_per_vehicle']:.1f}")
        print(f"   • Weather conditions: {result['data_quality']['weather_conditions']}")
        print(f"   • Route types: {result['data_quality']['route_types']}")
        
        print("\n🎯 Ready for ML model training with enhanced dataset!")
        
    finally:
        session.close()

if __name__ == "__main__":
    main()
