"""
Geospatial Analytics and Route Optimization for FleetFuel360
Advanced mapping and location-based fuel efficiency analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import json
import math

class GeoPoint:
    def __init__(self, latitude: float, longitude: float, timestamp: datetime = None):
        self.latitude = latitude
        self.longitude = longitude
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self):
        return {
            'lat': self.latitude,
            'lng': self.longitude,
            'timestamp': self.timestamp.isoformat()
        }

class Route:
    def __init__(self, vehicle_id: str, route_id: str = None):
        self.vehicle_id = vehicle_id
        self.route_id = route_id or f"route_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.waypoints: List[GeoPoint] = []
        self.fuel_consumption = 0.0
        self.total_distance = 0.0
        self.duration_minutes = 0
        self.efficiency_score = 0.0
        
    def add_waypoint(self, point: GeoPoint):
        self.waypoints.append(point)
        if len(self.waypoints) > 1:
            self.total_distance += self._calculate_distance(
                self.waypoints[-2], self.waypoints[-1]
            )
    
    def _calculate_distance(self, point1: GeoPoint, point2: GeoPoint) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        lat1, lon1 = math.radians(point1.latitude), math.radians(point1.longitude)
        lat2, lon2 = math.radians(point2.latitude), math.radians(point2.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def calculate_efficiency(self):
        """Calculate route efficiency"""
        if self.fuel_consumption > 0:
            self.efficiency_score = self.total_distance / self.fuel_consumption
        return self.efficiency_score

class GeospatialAnalytics:
    def __init__(self, db_session=None):
        self.session = db_session
        self.routes: List[Route] = []
        self.fuel_stations = self._load_fuel_stations()
        self.traffic_zones = self._load_traffic_zones()
        self.efficiency_heatmap = {}
        
    def _load_fuel_stations(self):
        """Load fuel station locations (mock data)"""
        # In production, this would load from a real database or API
        return [
            {'id': 'fs_001', 'name': 'Shell Station Downtown', 'lat': 40.7128, 'lng': -74.0060, 'price_per_liter': 1.45},
            {'id': 'fs_002', 'name': 'BP Highway', 'lat': 40.7589, 'lng': -73.9851, 'price_per_liter': 1.42},
            {'id': 'fs_003', 'name': 'Exxon Airport', 'lat': 40.6892, 'lng': -74.1745, 'price_per_liter': 1.48},
            {'id': 'fs_004', 'name': 'Mobil Industrial', 'lat': 40.6782, 'lng': -73.9442, 'price_per_liter': 1.41},
        ]
    
    def _load_traffic_zones(self):
        """Load traffic zone data (mock data)"""
        return [
            {
                'zone_id': 'downtown',
                'bounds': {'north': 40.8, 'south': 40.7, 'east': -73.9, 'west': -74.1},
                'avg_speed_kmh': 25,
                'congestion_factor': 1.3,
                'time_patterns': {
                    'rush_hour': [7, 8, 9, 17, 18, 19],
                    'congestion_multiplier': 1.8
                }
            },
            {
                'zone_id': 'highway',
                'bounds': {'north': 41.0, 'south': 40.5, 'east': -73.5, 'west': -74.5},
                'avg_speed_kmh': 80,
                'congestion_factor': 1.1,
                'time_patterns': {
                    'rush_hour': [7, 8, 9, 17, 18, 19],
                    'congestion_multiplier': 1.4
                }
            }
        ]
    
    def analyze_route_efficiency(self, route: Route, fuel_data: Dict) -> Dict:
        """Analyze route efficiency with geospatial context"""
        analysis = {
            'route_id': route.route_id,
            'vehicle_id': route.vehicle_id,
            'total_distance_km': route.total_distance,
            'fuel_consumed_l': fuel_data.get('fuel_used', 0),
            'efficiency_kmpl': 0,
            'zones_traversed': [],
            'traffic_impact': {},
            'optimization_opportunities': []
        }
        
        if fuel_data.get('fuel_used', 0) > 0:
            analysis['efficiency_kmpl'] = route.total_distance / fuel_data['fuel_used']
        
        # Analyze zones traversed
        for waypoint in route.waypoints:
            zone = self._get_traffic_zone(waypoint)
            if zone and zone['zone_id'] not in [z['zone_id'] for z in analysis['zones_traversed']]:
                analysis['zones_traversed'].append(zone)
        
        # Calculate traffic impact
        analysis['traffic_impact'] = self._calculate_traffic_impact(route)
        
        # Find optimization opportunities
        analysis['optimization_opportunities'] = self._find_optimization_opportunities(route, analysis)
        
        return analysis
    
    def generate_efficiency_heatmap(self, routes_data: List[Dict]) -> Dict:
        """Generate heatmap data for fuel efficiency by location"""
        heatmap_data = {}
        
        # Create grid for heatmap (simplified version)
        lat_min, lat_max = 40.5, 41.0
        lng_min, lng_max = -74.5, -73.5
        grid_size = 0.01  # ~1km resolution
        
        # Initialize grid
        lat_steps = int((lat_max - lat_min) / grid_size)
        lng_steps = int((lng_max - lng_min) / grid_size)
        
        for route_data in routes_data:
            if not route_data.get('waypoints'):
                continue
                
            efficiency = route_data.get('fuel_efficiency', 0)
            
            for waypoint in route_data['waypoints']:
                # Assign efficiency to grid cell
                lat_idx = int((waypoint['lat'] - lat_min) / grid_size)
                lng_idx = int((waypoint['lng'] - lng_min) / grid_size)
                
                grid_key = f"{lat_idx}_{lng_idx}"
                
                if grid_key not in heatmap_data:
                    heatmap_data[grid_key] = {
                        'lat': lat_min + lat_idx * grid_size,
                        'lng': lng_min + lng_idx * grid_size,
                        'efficiency_sum': 0,
                        'count': 0,
                        'avg_efficiency': 0
                    }
                
                heatmap_data[grid_key]['efficiency_sum'] += efficiency
                heatmap_data[grid_key]['count'] += 1
                heatmap_data[grid_key]['avg_efficiency'] = (
                    heatmap_data[grid_key]['efficiency_sum'] / 
                    heatmap_data[grid_key]['count']
                )
        
        # Convert to list format for frontend
        heatmap_points = []
        for grid_key, data in heatmap_data.items():
            if data['count'] >= 3:  # Only include cells with sufficient data
                heatmap_points.append({
                    'lat': data['lat'],
                    'lng': data['lng'],
                    'efficiency': data['avg_efficiency'],
                    'intensity': min(data['count'] / 10.0, 1.0),  # Normalize intensity
                    'color': self._get_efficiency_color(data['avg_efficiency'])
                })
        
        return {
            'heatmap_points': heatmap_points,
            'metadata': {
                'total_points': len(heatmap_points),
                'avg_efficiency': np.mean([p['efficiency'] for p in heatmap_points]) if heatmap_points else 0,
                'efficiency_range': {
                    'min': min([p['efficiency'] for p in heatmap_points]) if heatmap_points else 0,
                    'max': max([p['efficiency'] for p in heatmap_points]) if heatmap_points else 0
                }
            }
        }
    
    def optimize_route(self, start_point: GeoPoint, end_point: GeoPoint, 
                      constraints: Dict = None) -> Dict:
        """Optimize route for fuel efficiency"""
        constraints = constraints or {}
        
        # Simplified route optimization (in production, use Google Maps API or similar)
        optimization_result = {
            'original_route': {
                'distance_km': self._calculate_distance(start_point, end_point),
                'estimated_fuel_l': 0,
                'estimated_time_minutes': 0
            },
            'optimized_route': {
                'waypoints': [],
                'distance_km': 0,
                'estimated_fuel_l': 0,
                'estimated_time_minutes': 0,
                'fuel_savings_l': 0,
                'time_difference_minutes': 0
            },
            'recommendations': []
        }
        
        # Calculate original route metrics
        original_distance = optimization_result['original_route']['distance_km']
        avg_efficiency = constraints.get('vehicle_efficiency', 7.5)  # km/L
        
        optimization_result['original_route']['estimated_fuel_l'] = original_distance / avg_efficiency
        optimization_result['original_route']['estimated_time_minutes'] = (original_distance / 50) * 60  # Assume 50 km/h avg
        
        # Find optimal fuel stops
        fuel_stops = self._find_optimal_fuel_stops(start_point, end_point, constraints)
        
        # Generate optimized waypoints
        optimized_waypoints = [start_point.to_dict()]
        optimized_waypoints.extend([stop['location'] for stop in fuel_stops])
        optimized_waypoints.append(end_point.to_dict())
        
        # Calculate optimized route metrics
        optimized_distance = self._calculate_route_distance(optimized_waypoints)
        efficiency_improvement = constraints.get('route_efficiency_factor', 1.05)  # 5% improvement
        
        optimization_result['optimized_route']['waypoints'] = optimized_waypoints
        optimization_result['optimized_route']['distance_km'] = optimized_distance
        optimization_result['optimized_route']['estimated_fuel_l'] = optimized_distance / (avg_efficiency * efficiency_improvement)
        optimization_result['optimized_route']['estimated_time_minutes'] = self._calculate_route_time(optimized_waypoints)
        
        # Calculate savings
        optimization_result['optimized_route']['fuel_savings_l'] = (
            optimization_result['original_route']['estimated_fuel_l'] - 
            optimization_result['optimized_route']['estimated_fuel_l']
        )
        
        optimization_result['optimized_route']['time_difference_minutes'] = (
            optimization_result['optimized_route']['estimated_time_minutes'] - 
            optimization_result['original_route']['estimated_time_minutes']
        )
        
        # Generate recommendations
        optimization_result['recommendations'] = self._generate_route_recommendations(
            optimization_result, fuel_stops
        )
        
        return optimization_result
    
    def optimize_routes(self) -> Dict:
        """Optimize routes for better fuel efficiency"""
        try:
            # Sample route optimization results
            # In production, this would use advanced routing algorithms
            
            optimization_results = {
                'total_routes_analyzed': 25,
                'routes_optimized': 18,
                'optimization_summary': {
                    'fuel_savings_percentage': 12.5,
                    'distance_reduction_percentage': 8.3,
                    'time_savings_minutes': 145,
                    'estimated_monthly_savings': 3250.00
                },
                'optimized_routes': [
                    {
                        'route_id': 'R-001',
                        'original_distance': 125.6,
                        'optimized_distance': 118.2,
                        'fuel_savings': 2.4,
                        'optimization_type': 'traffic_avoidance'
                    },
                    {
                        'route_id': 'R-007', 
                        'original_distance': 89.3,
                        'optimized_distance': 82.1,
                        'fuel_savings': 1.8,
                        'optimization_type': 'route_consolidation'
                    },
                    {
                        'route_id': 'R-012',
                        'original_distance': 156.8,
                        'optimized_distance': 143.7,
                        'fuel_savings': 3.2,
                        'optimization_type': 'fuel_station_optimization'
                    }
                ],
                'recommendations': [
                    'Implement real-time traffic monitoring',
                    'Consider delivery time window adjustments',
                    'Optimize fuel station stop locations'
                ]
            }
            
            return optimization_results
            
        except Exception as e:
            print(f"Error optimizing routes: {e}")
            return {}

    def analyze_route_efficiency(self) -> Dict:
        """Analyze route efficiency patterns"""
        try:
            # Sample route efficiency analysis
            efficiency_analysis = {
                'analysis_period': '30 days',
                'total_routes': 245,
                'efficiency_metrics': {
                    'average_mpg_per_route': 9.7,
                    'best_performing_route': {'id': 'R-003', 'mpg': 12.8},
                    'worst_performing_route': {'id': 'R-018', 'mpg': 6.2},
                    'efficiency_variance': 2.4
                },
                'geographic_patterns': {
                    'urban_efficiency': 8.1,
                    'suburban_efficiency': 11.2,
                    'highway_efficiency': 12.5,
                    'construction_zone_impact': -18.5
                },
                'improvement_opportunities': {
                    'route_consolidation': 15,
                    'traffic_pattern_optimization': 12,
                    'fuel_station_placement': 8
                }
            }
            
            return efficiency_analysis
            
        except Exception as e:
            print(f"Error analyzing route efficiency: {e}")
            return {}

    def get_efficiency_heatmap(self) -> List[Dict]:
        """Generate efficiency heatmap data"""
        try:
            # Sample heatmap data points
            heatmap_data = [
                {'lat': 40.7128, 'lng': -74.0060, 'efficiency': 9.2, 'intensity': 0.8},
                {'lat': 40.7589, 'lng': -73.9851, 'efficiency': 11.5, 'intensity': 0.6},
                {'lat': 40.6892, 'lng': -74.0445, 'efficiency': 8.7, 'intensity': 0.9},
                {'lat': 40.7831, 'lng': -73.9712, 'efficiency': 10.8, 'intensity': 0.5},
                {'lat': 40.7282, 'lng': -73.7949, 'efficiency': 12.1, 'intensity': 0.4},
                {'lat': 40.6782, 'lng': -73.9442, 'efficiency': 9.8, 'intensity': 0.7},
                {'lat': 40.8176, 'lng': -73.9782, 'efficiency': 10.2, 'intensity': 0.6},
                {'lat': 40.7505, 'lng': -73.9934, 'efficiency': 8.9, 'intensity': 0.8}
            ]
            
            return heatmap_data
            
        except Exception as e:
            print(f"Error generating heatmap: {e}")
            return []

    def analyze_driver_behavior_by_location(self, driver_data: List[Dict]) -> Dict:
        """Analyze driver behavior patterns by location"""
        behavior_analysis = {
            'by_zone': {},
            'efficiency_patterns': {},
            'recommendations': []
        }
        
        for data in driver_data:
            zone = self._get_traffic_zone_by_coords(data.get('lat', 0), data.get('lng', 0))
            zone_id = zone['zone_id'] if zone else 'unknown'
            
            if zone_id not in behavior_analysis['by_zone']:
                behavior_analysis['by_zone'][zone_id] = {
                    'trips_count': 0,
                    'avg_efficiency': 0,
                    'efficiency_variance': 0,
                    'speed_patterns': [],
                    'fuel_consumption': 0
                }
            
            zone_data = behavior_analysis['by_zone'][zone_id]
            zone_data['trips_count'] += 1
            zone_data['avg_efficiency'] = (
                (zone_data['avg_efficiency'] * (zone_data['trips_count'] - 1) + 
                 data.get('fuel_efficiency', 0)) / zone_data['trips_count']
            )
            zone_data['fuel_consumption'] += data.get('fuel_used', 0)
            
            if 'speed' in data:
                zone_data['speed_patterns'].append(data['speed'])
        
        # Generate efficiency patterns
        for zone_id, zone_data in behavior_analysis['by_zone'].items():
            if zone_data['trips_count'] > 0:
                behavior_analysis['efficiency_patterns'][zone_id] = {
                    'efficiency_rating': self._rate_efficiency(zone_data['avg_efficiency']),
                    'consistency': self._calculate_consistency(zone_data.get('speed_patterns', [])),
                    'improvement_potential': self._calculate_improvement_potential(zone_data)
                }
        
        # Generate recommendations
        behavior_analysis['recommendations'] = self._generate_behavior_recommendations(behavior_analysis)
        
        return behavior_analysis
    
    def _get_traffic_zone(self, point: GeoPoint) -> Optional[Dict]:
        """Get traffic zone for a given point"""
        for zone in self.traffic_zones:
            bounds = zone['bounds']
            if (bounds['south'] <= point.latitude <= bounds['north'] and
                bounds['west'] <= point.longitude <= bounds['east']):
                return zone
        return None
    
    def _get_traffic_zone_by_coords(self, lat: float, lng: float) -> Optional[Dict]:
        """Get traffic zone by coordinates"""
        point = GeoPoint(lat, lng)
        return self._get_traffic_zone(point)
    
    def _calculate_traffic_impact(self, route: Route) -> Dict:
        """Calculate traffic impact on route"""
        impact = {
            'congestion_factor': 1.0,
            'time_penalty_minutes': 0,
            'fuel_penalty_percent': 0,
            'peak_hours_traversed': []
        }
        
        for waypoint in route.waypoints:
            zone = self._get_traffic_zone(waypoint)
            if zone:
                hour = waypoint.timestamp.hour if waypoint.timestamp else 12
                
                if hour in zone['time_patterns']['rush_hour']:
                    impact['congestion_factor'] = max(
                        impact['congestion_factor'],
                        zone['time_patterns']['congestion_multiplier']
                    )
                    impact['peak_hours_traversed'].append(hour)
        
        impact['fuel_penalty_percent'] = (impact['congestion_factor'] - 1.0) * 100
        impact['time_penalty_minutes'] = route.duration_minutes * (impact['congestion_factor'] - 1.0)
        
        return impact
    
    def _find_optimization_opportunities(self, route: Route, analysis: Dict) -> List[Dict]:
        """Find opportunities to optimize the route"""
        opportunities = []
        
        # Check for high-congestion areas
        if analysis['traffic_impact']['congestion_factor'] > 1.5:
            opportunities.append({
                'type': 'avoid_congestion',
                'description': 'Route passes through high-congestion areas',
                'potential_savings': f"{analysis['traffic_impact']['fuel_penalty_percent']:.1f}% fuel reduction",
                'recommendation': 'Consider alternative routes during peak hours'
            })
        
        # Check for fuel station optimization
        nearest_cheap_station = min(self.fuel_stations, key=lambda x: x['price_per_liter'])
        opportunities.append({
            'type': 'fuel_cost_optimization',
            'description': f'Fuel available at {nearest_cheap_station["name"]}',
            'potential_savings': f'${(max([s["price_per_liter"] for s in self.fuel_stations]) - nearest_cheap_station["price_per_liter"]) * analysis.get("fuel_consumed_l", 20):.2f} per tank',
            'recommendation': f'Refuel at {nearest_cheap_station["name"]}'
        })
        
        # Check for efficiency improvements
        if analysis['efficiency_kmpl'] < 6.0:
            opportunities.append({
                'type': 'efficiency_improvement',
                'description': 'Below-average fuel efficiency detected',
                'potential_savings': '15-20% fuel reduction possible',
                'recommendation': 'Review driving patterns and vehicle maintenance'
            })
        
        return opportunities
    
    def _find_optimal_fuel_stops(self, start: GeoPoint, end: GeoPoint, constraints: Dict) -> List[Dict]:
        """Find optimal fuel stops along route"""
        fuel_stops = []
        
        # Find stations along the route (simplified)
        for station in self.fuel_stations:
            station_point = GeoPoint(station['lat'], station['lng'])
            
            # Check if station is reasonably along the route
            detour_distance = (self._calculate_distance(start, station_point) + 
                             self._calculate_distance(station_point, end))
            direct_distance = self._calculate_distance(start, end)
            
            if detour_distance <= direct_distance * 1.2:  # Max 20% detour
                fuel_stops.append({
                    'station_id': station['id'],
                    'location': station_point.to_dict(),
                    'price_per_liter': station['price_per_liter'],
                    'detour_km': detour_distance - direct_distance,
                    'savings_potential': self._calculate_fuel_savings(station, constraints)
                })
        
        # Sort by savings potential
        fuel_stops.sort(key=lambda x: x['savings_potential'], reverse=True)
        
        return fuel_stops[:2]  # Return top 2 stops
    
    def _calculate_route_distance(self, waypoints: List[Dict]) -> float:
        """Calculate total distance for route with waypoints"""
        total_distance = 0
        
        for i in range(len(waypoints) - 1):
            point1 = GeoPoint(waypoints[i]['lat'], waypoints[i]['lng'])
            point2 = GeoPoint(waypoints[i+1]['lat'], waypoints[i+1]['lng'])
            total_distance += self._calculate_distance(point1, point2)
        
        return total_distance
    
    def _calculate_route_time(self, waypoints: List[Dict]) -> float:
        """Calculate estimated route time"""
        total_time = 0
        
        for i in range(len(waypoints) - 1):
            point1 = GeoPoint(waypoints[i]['lat'], waypoints[i]['lng'])
            point2 = GeoPoint(waypoints[i+1]['lat'], waypoints[i+1]['lng'])
            
            distance = self._calculate_distance(point1, point2)
            zone = self._get_traffic_zone(point1)
            avg_speed = zone['avg_speed_kmh'] if zone else 50
            
            total_time += (distance / avg_speed) * 60  # Convert to minutes
        
        return total_time
    
    def _calculate_fuel_savings(self, station: Dict, constraints: Dict) -> float:
        """Calculate potential fuel savings at station"""
        avg_price = np.mean([s['price_per_liter'] for s in self.fuel_stations])
        price_savings = avg_price - station['price_per_liter']
        tank_size = constraints.get('tank_size', 100)  # Liters
        
        return price_savings * tank_size
    
    def _get_efficiency_color(self, efficiency: float) -> str:
        """Get color code for efficiency level"""
        if efficiency >= 8.0:
            return '#00ff00'  # Green - Excellent
        elif efficiency >= 7.0:
            return '#ffff00'  # Yellow - Good
        elif efficiency >= 6.0:
            return '#ff8800'  # Orange - Average
        else:
            return '#ff0000'  # Red - Poor
    
    def _rate_efficiency(self, efficiency: float) -> str:
        """Rate efficiency level"""
        if efficiency >= 8.0:
            return 'excellent'
        elif efficiency >= 7.0:
            return 'good'
        elif efficiency >= 6.0:
            return 'average'
        else:
            return 'poor'
    
    def _calculate_consistency(self, speed_patterns: List[float]) -> str:
        """Calculate driving consistency"""
        if not speed_patterns:
            return 'unknown'
        
        variance = np.var(speed_patterns)
        if variance < 25:
            return 'consistent'
        elif variance < 100:
            return 'moderate'
        else:
            return 'inconsistent'
    
    def _calculate_improvement_potential(self, zone_data: Dict) -> str:
        """Calculate improvement potential"""
        efficiency = zone_data['avg_efficiency']
        
        if efficiency < 6.0:
            return 'high'
        elif efficiency < 7.5:
            return 'medium'
        else:
            return 'low'
    
    def _generate_route_recommendations(self, optimization_result: Dict, fuel_stops: List[Dict]) -> List[str]:
        """Generate route recommendations"""
        recommendations = []
        
        fuel_savings = optimization_result['optimized_route']['fuel_savings_l']
        time_difference = optimization_result['optimized_route']['time_difference_minutes']
        
        if fuel_savings > 2.0:
            recommendations.append(f"Optimized route saves {fuel_savings:.1f}L of fuel")
        
        if time_difference < 15:
            recommendations.append("Route optimization adds minimal travel time")
        
        if fuel_stops:
            cheapest_stop = min(fuel_stops, key=lambda x: x['price_per_liter'])
            recommendations.append(f"Refuel at {cheapest_stop['station_id']} for best prices")
        
        return recommendations
    
    def _generate_behavior_recommendations(self, behavior_analysis: Dict) -> List[str]:
        """Generate driver behavior recommendations"""
        recommendations = []
        
        for zone_id, patterns in behavior_analysis['efficiency_patterns'].items():
            if patterns['efficiency_rating'] == 'poor':
                recommendations.append(f"Focus on improving efficiency in {zone_id} zone")
            
            if patterns['consistency'] == 'inconsistent':
                recommendations.append(f"Maintain consistent speed in {zone_id} zone")
            
            if patterns['improvement_potential'] == 'high':
                recommendations.append(f"High improvement potential in {zone_id} zone")
        
        return recommendations

# Example usage and demonstration
if __name__ == "__main__":
    # Initialize geospatial analytics
    geo_analytics = GeospatialAnalytics()
    
    # Create sample route
    route = Route('TRUCK001')
    
    # Add waypoints (simulating a trip through NYC)
    waypoints = [
        GeoPoint(40.7128, -74.0060, datetime.now()),  # Manhattan
        GeoPoint(40.7589, -73.9851, datetime.now() + timedelta(minutes=30)),  # Central Park
        GeoPoint(40.6892, -74.1745, datetime.now() + timedelta(hours=1)),  # Newark Airport
    ]
    
    for waypoint in waypoints:
        route.add_waypoint(waypoint)
    
    # Analyze route
    fuel_data = {'fuel_used': 15.5}
    analysis = geo_analytics.analyze_route_efficiency(route, fuel_data)
    
    print("🗺️  Route Analysis:")
    print(f"   Distance: {analysis['total_distance_km']:.1f} km")
    print(f"   Efficiency: {analysis['efficiency_kmpl']:.2f} km/L")
    print(f"   Zones: {[z['zone_id'] for z in analysis['zones_traversed']]}")
    print(f"   Opportunities: {len(analysis['optimization_opportunities'])}")
    
    # Optimize route
    start = GeoPoint(40.7128, -74.0060)
    end = GeoPoint(40.6892, -74.1745)
    
    optimization = geo_analytics.optimize_route(start, end, {'vehicle_efficiency': 7.5})
    
    print(f"\n🎯 Route Optimization:")
    print(f"   Fuel savings: {optimization['optimized_route']['fuel_savings_l']:.1f}L")
    print(f"   Time difference: {optimization['optimized_route']['time_difference_minutes']:.0f} minutes")
    print(f"   Recommendations: {len(optimization['recommendations'])}")
    
    # Generate efficiency heatmap (mock data)
    mock_routes_data = [
        {
            'waypoints': [{'lat': 40.7128 + i*0.01, 'lng': -74.0060 + i*0.01} for i in range(10)],
            'fuel_efficiency': 7.5 + np.random.normal(0, 0.5)
        }
        for _ in range(50)
    ]
    
    heatmap = geo_analytics.generate_efficiency_heatmap(mock_routes_data)
    print(f"\n🔥 Efficiency Heatmap: {heatmap['metadata']['total_points']} data points")
    print(f"   Average efficiency: {heatmap['metadata']['avg_efficiency']:.2f} km/L")
