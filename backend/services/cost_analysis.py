"""
Cost Analysis and ROI Calculator for FleetFuel360
Financial analysis tools for fleet fuel optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

class FuelPriceTracker:
    def __init__(self):
        self.price_history = {}
        self.current_prices = self._load_current_prices()
        self.price_trends = {}
    
    def _load_current_prices(self):
        """Load current fuel prices (mock data - in production, use real API)"""
        return {
            'diesel': 1.45,  # USD per liter
            'gasoline': 1.38,
            'biodiesel': 1.52,
            'lng': 0.95
        }
    
    def update_price(self, fuel_type: str, price: float, station_id: str = None):
        """Update fuel price"""
        if fuel_type not in self.price_history:
            self.price_history[fuel_type] = []
        
        self.price_history[fuel_type].append({
            'timestamp': datetime.now(),
            'price': price,
            'station_id': station_id
        })
        
        self.current_prices[fuel_type] = price
    def get_price_trend(self, fuel_type: str, days: int = 30) -> Dict:
        """Get price trend for fuel type"""
        if fuel_type not in self.price_history:
            return {'trend': 'stable', 'change_percent': 0}
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_prices = [
            p for p in self.price_history[fuel_type] 
            if p['timestamp'] >= cutoff_date
        ]
        
        if len(recent_prices) < 2:
            return {'trend': 'insufficient_data', 'change_percent': 0}
        
        first_price = recent_prices[0]['price']
        last_price = recent_prices[-1]['price']
        change_percent = ((last_price - first_price) / first_price) * 100
        
        trend = 'increasing' if change_percent > 2 else 'decreasing' if change_percent < -2 else 'stable'
        
        return {
            'trend': trend,
            'change_percent': change_percent,
            'current_price': last_price,
            'period_start_price': first_price,
            'volatility': np.std([p['price'] for p in recent_prices])
        }

class CostAnalyzer:
    def __init__(self, db_session=None):
        self.session = db_session
        self.fuel_tracker = FuelPriceTracker()
        self.operational_costs = self._load_operational_costs()
        self.vehicle_depreciation = self._load_depreciation_rates()
    
    def _load_operational_costs(self):
        """Load operational cost factors"""
        return {
            'maintenance_per_km': 0.08,  # USD per km
            'insurance_monthly': 450,    # USD per vehicle per month
            'driver_salary_hourly': 25,  # USD per hour
            'tire_replacement_per_km': 0.02,
            'vehicle_registration_annual': 500,
            'tracking_system_monthly': 45
        }
    
    def _load_depreciation_rates(self):
        """Load vehicle depreciation rates by type"""
        return {
            'light_truck': {'annual_rate': 0.15, 'useful_life_years': 8},
            'heavy_truck': {'annual_rate': 0.12, 'useful_life_years': 12},
            'van': {'annual_rate': 0.18, 'useful_life_years': 6},
            'trailer': {'annual_rate': 0.08, 'useful_life_years': 15}
        }
    
    def calculate_trip_cost(self, trip_data: Dict) -> Dict:
        """Calculate comprehensive cost for a single trip"""
        costs = {
            'fuel_cost': 0,
            'maintenance_cost': 0,
            'driver_cost': 0,
            'depreciation_cost': 0,
            'total_cost': 0,
            'cost_per_km': 0
        }
        
        # Fuel cost
        fuel_used = trip_data.get('fuel_used', 0)
        fuel_type = trip_data.get('fuel_type', 'diesel')
        fuel_price = self.fuel_tracker.current_prices.get(fuel_type, 1.45)
        costs['fuel_cost'] = fuel_used * fuel_price
        
        # Maintenance cost
        km_driven = trip_data.get('km_driven', 0)
        costs['maintenance_cost'] = km_driven * self.operational_costs['maintenance_per_km']
        
        # Driver cost
        trip_duration_hours = trip_data.get('duration_hours', km_driven / 50)  # Assume 50 km/h avg
        costs['driver_cost'] = trip_duration_hours * self.operational_costs['driver_salary_hourly']
        
        # Depreciation cost
        vehicle_type = trip_data.get('vehicle_type', 'heavy_truck')
        depreciation_rate = self.vehicle_depreciation.get(vehicle_type, {}).get('annual_rate', 0.12)
        vehicle_value = trip_data.get('vehicle_value', 80000)  # USD
        daily_depreciation = (vehicle_value * depreciation_rate) / 365
        costs['depreciation_cost'] = daily_depreciation
        
        # Total cost
        costs['total_cost'] = sum([
            costs['fuel_cost'],
            costs['maintenance_cost'],
            costs['driver_cost'],
            costs['depreciation_cost']
        ])
        
        # Cost per km
        costs['cost_per_km'] = costs['total_cost'] / km_driven if km_driven > 0 else 0
        
        return costs
    
    def calculate_fleet_costs(self, fleet_data: List[Dict], period_days: int = 30) -> Dict:
        """Calculate comprehensive fleet costs for a period"""
        fleet_costs = {
            'total_fuel_cost': 0,
            'total_maintenance_cost': 0,
            'total_driver_cost': 0,
            'total_operational_cost': 0,
            'total_depreciation_cost': 0,
            'grand_total': 0,
            'cost_breakdown_by_vehicle': {},
            'cost_trends': {},
            'efficiency_metrics': {}
        }
        
        # Calculate costs for each vehicle
        for vehicle_data in fleet_data:
            vehicle_id = vehicle_data['vehicle_id']
            trip_costs = []
            
            for trip in vehicle_data.get('trips', []):
                trip_cost = self.calculate_trip_cost(trip)
                trip_costs.append(trip_cost)
            
            # Aggregate vehicle costs
            vehicle_total = {
                'fuel_cost': sum(t['fuel_cost'] for t in trip_costs),
                'maintenance_cost': sum(t['maintenance_cost'] for t in trip_costs),
                'driver_cost': sum(t['driver_cost'] for t in trip_costs),
                'depreciation_cost': sum(t['depreciation_cost'] for t in trip_costs),
                'trip_count': len(trip_costs),
                'total_km': sum(trip.get('km_driven', 0) for trip in vehicle_data.get('trips', [])),
                'total_fuel': sum(trip.get('fuel_used', 0) for trip in vehicle_data.get('trips', []))
            }
            
            vehicle_total['total_cost'] = sum([
                vehicle_total['fuel_cost'],
                vehicle_total['maintenance_cost'],
                vehicle_total['driver_cost'],
                vehicle_total['depreciation_cost']
            ])
            
            vehicle_total['cost_per_km'] = (
                vehicle_total['total_cost'] / vehicle_total['total_km'] 
                if vehicle_total['total_km'] > 0 else 0
            )
            
            fleet_costs['cost_breakdown_by_vehicle'][vehicle_id] = vehicle_total
            
            # Add to fleet totals
            fleet_costs['total_fuel_cost'] += vehicle_total['fuel_cost']
            fleet_costs['total_maintenance_cost'] += vehicle_total['maintenance_cost']
            fleet_costs['total_driver_cost'] += vehicle_total['driver_cost']
            fleet_costs['total_depreciation_cost'] += vehicle_total['depreciation_cost']
        
        # Calculate additional operational costs
        num_vehicles = len(fleet_data)
        monthly_operational = (
            num_vehicles * self.operational_costs['insurance_monthly'] +
            num_vehicles * self.operational_costs['tracking_system_monthly']
        )
        
        fleet_costs['total_operational_cost'] = monthly_operational * (period_days / 30)
        
        # Grand total
        fleet_costs['grand_total'] = sum([
            fleet_costs['total_fuel_cost'],
            fleet_costs['total_maintenance_cost'],
            fleet_costs['total_driver_cost'],
            fleet_costs['total_operational_cost'],
            fleet_costs['total_depreciation_cost']
        ])
        
        # Calculate efficiency metrics
        total_km = sum(v['total_km'] for v in fleet_costs['cost_breakdown_by_vehicle'].values())
        total_fuel = sum(v['total_fuel'] for v in fleet_costs['cost_breakdown_by_vehicle'].values())
        
        fleet_costs['efficiency_metrics'] = {
            'fleet_avg_efficiency': total_km / total_fuel if total_fuel > 0 else 0,
            'fleet_avg_cost_per_km': fleet_costs['grand_total'] / total_km if total_km > 0 else 0,
            'fuel_cost_percentage': (fleet_costs['total_fuel_cost'] / fleet_costs['grand_total']) * 100 if fleet_costs['grand_total'] > 0 else 0
        }
        
        return fleet_costs

    def calculate_delivery_costs(self) -> Dict:
        """Calculate cost per delivery for logistics operations"""
        try:
            # Sample delivery cost calculation
            # In production, this would analyze actual delivery data
            
            delivery_metrics = {
                'total_deliveries': 1250,
                'total_fuel_cost': 18500.00,
                'total_miles': 45600,
                'average_deliveries_per_day': 35,
                'cost_per_delivery': 18500.00 / 1250,  # $14.80 per delivery
                'fuel_cost_per_mile': 18500.00 / 45600,  # $0.406 per mile
                'delivery_efficiency_score': 87.3,
                'optimization_potential': {
                    'route_optimization_savings': 2100.00,  # Potential monthly savings
                    'delivery_consolidation_savings': 1350.00,
                    'fuel_efficiency_improvements': 850.00
                }
            }
            
            return delivery_metrics
            
        except Exception as e:
            print(f"Error calculating delivery costs: {e}")
            return {}

    def get_comprehensive_cost_analysis(self, days_back: int = 30) -> Dict:
        """Get comprehensive cost analysis for the specified period"""
        try:
            # Sample comprehensive cost analysis
            # In production, this would analyze actual fleet data
            
            total_fuel_cost = 18500.00 * (days_back / 30)  # Scale by period
            total_maintenance_cost = 5200.00 * (days_back / 30)
            total_operational_cost = 3800.00 * (days_back / 30)
            
            analysis = {
                'period_days': days_back,
                'total_costs': {
                    'fuel_cost': total_fuel_cost,
                    'maintenance_cost': total_maintenance_cost,
                    'operational_cost': total_operational_cost,
                    'total': total_fuel_cost + total_maintenance_cost + total_operational_cost
                },
                'efficiency_metrics': {
                    'cost_per_mile': 0.406,
                    'cost_per_gallon': 3.85,
                    'fuel_efficiency_mpg': 9.8
                },
                'cost_breakdown': {
                    'fuel_percentage': 68.5,
                    'maintenance_percentage': 19.2,
                    'operational_percentage': 12.3
                },
                'projections': {
                    'monthly_fuel_cost': total_fuel_cost * (30 / days_back),
                    'annual_fuel_cost': total_fuel_cost * (365 / days_back)
                },
                'optimization_opportunities': {
                    'potential_monthly_savings': 2850.00,
                    'route_optimization': 1200.00,
                    'fuel_efficiency_improvements': 950.00,
                    'maintenance_optimization': 700.00
                }
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error in comprehensive cost analysis: {e}")
            return {}
    
    def calculate_fleet_roi(self, days_back: int = 30) -> Dict:
        """Calculate ROI metrics for the fleet"""
        try:
            # Sample ROI calculation
            # In production, this would use actual investment and savings data
            
            roi_analysis = {
                'investment_analysis': {
                    'initial_investment': 485000.00,  # Fleet purchase cost
                    'operational_investment': 125000.00,  # Annual operational costs
                    'technology_investment': 15000.00  # FleetFuel360 system
                },
                'returns': {
                    'fuel_savings_annual': 45000.00,
                    'maintenance_savings_annual': 18500.00,
                    'efficiency_gains_annual': 12800.00,
                    'total_annual_savings': 76300.00
                },
                'roi_metrics': {
                    'roi_percentage': 12.2,  # Annual ROI
                    'payback_period_months': 9.8,
                    'net_present_value': 125400.00,
                    'break_even_point': '9.8 months'
                },
                'performance_indicators': {
                    'cost_reduction_percentage': 15.7,
                    'efficiency_improvement_percentage': 18.3,
                    'maintenance_cost_reduction': 22.1
                }
            }
            
            return roi_analysis
            
        except Exception as e:
            print(f"Error calculating fleet ROI: {e}")
            return {}

class ROICalculator:
    def __init__(self):
        self.cost_analyzer = CostAnalyzer()
    
    def calculate_fuel_optimization_roi(self, optimization_data: Dict) -> Dict:
        """Calculate ROI for fuel optimization initiatives"""
        
        # Investment costs
        investment = {
            'system_implementation': optimization_data.get('system_cost', 25000),
            'driver_training': optimization_data.get('training_cost', 5000),
            'vehicle_upgrades': optimization_data.get('upgrade_cost', 15000),
            'monitoring_setup': optimization_data.get('monitoring_cost', 8000),
            'total_investment': 0
        }
        
        investment['total_investment'] = sum(investment.values()) - investment['total_investment']
        
        # Expected savings
        baseline_data = optimization_data.get('baseline', {})
        projected_data = optimization_data.get('projected', {})
        
        annual_baseline_cost = baseline_data.get('annual_fuel_cost', 150000)
        efficiency_improvement = projected_data.get('efficiency_improvement_percent', 15)
        annual_fuel_savings = annual_baseline_cost * (efficiency_improvement / 100)
        
        # Additional savings
        maintenance_savings = baseline_data.get('annual_maintenance_cost', 40000) * 0.1  # 10% reduction
        downtime_savings = baseline_data.get('downtime_cost_annual', 20000) * 0.2  # 20% reduction
        
        total_annual_savings = annual_fuel_savings + maintenance_savings + downtime_savings
        
        # ROI calculations
        roi_metrics = {
            'investment_breakdown': investment,
            'annual_savings_breakdown': {
                'fuel_savings': annual_fuel_savings,
                'maintenance_savings': maintenance_savings,
                'downtime_savings': downtime_savings,
                'total_annual_savings': total_annual_savings
            },
            'roi_metrics': {
                'payback_period_months': (investment['total_investment'] / total_annual_savings) * 12 if total_annual_savings > 0 else float('inf'),
                'annual_roi_percent': ((total_annual_savings - investment['total_investment'] / 5) / investment['total_investment']) * 100,  # Assuming 5-year depreciation
                'net_present_value_5_years': self._calculate_npv(investment['total_investment'], total_annual_savings, 5, 0.08),
                'break_even_efficiency_improvement': (investment['total_investment'] / annual_baseline_cost) * 100
            },
            'sensitivity_analysis': self._perform_sensitivity_analysis(investment['total_investment'], annual_baseline_cost, efficiency_improvement)
        }
        
        return roi_metrics
    
    def calculate_vehicle_replacement_roi(self, vehicle_data: Dict) -> Dict:
        """Calculate ROI for vehicle replacement"""
        
        current_vehicle = vehicle_data.get('current', {})
        replacement_vehicle = vehicle_data.get('replacement', {})
        
        # Current vehicle costs (annual)
        current_costs = {
            'fuel_cost': current_vehicle.get('annual_fuel_cost', 18000),
            'maintenance_cost': current_vehicle.get('annual_maintenance_cost', 8000),
            'downtime_cost': current_vehicle.get('annual_downtime_cost', 5000),
            'depreciation': current_vehicle.get('current_value', 30000) * 0.15,  # 15% annual depreciation
            'total_annual_cost': 0
        }
        current_costs['total_annual_cost'] = sum(current_costs.values()) - current_costs['total_annual_cost']
        
        # Replacement vehicle costs (annual)
        replacement_costs = {
            'fuel_cost': replacement_vehicle.get('annual_fuel_cost', 14000),  # More efficient
            'maintenance_cost': replacement_vehicle.get('annual_maintenance_cost', 4000),  # Newer, less maintenance
            'downtime_cost': replacement_vehicle.get('annual_downtime_cost', 2000),  # More reliable
            'depreciation': replacement_vehicle.get('purchase_price', 80000) * 0.18,  # Higher depreciation for new vehicle
            'loan_payment': replacement_vehicle.get('annual_loan_payment', 16000),
            'total_annual_cost': 0
        }
        replacement_costs['total_annual_cost'] = sum(replacement_costs.values()) - replacement_costs['total_annual_cost']
        
        # Calculate savings and ROI
        annual_savings = current_costs['total_annual_cost'] - replacement_costs['total_annual_cost']
        down_payment = replacement_vehicle.get('down_payment', 20000)
        
        replacement_roi = {
            'cost_comparison': {
                'current_vehicle_annual_cost': current_costs,
                'replacement_vehicle_annual_cost': replacement_costs,
                'annual_savings': annual_savings
            },
            'investment_analysis': {
                'down_payment': down_payment,
                'payback_period_months': (down_payment / annual_savings) * 12 if annual_savings > 0 else float('inf'),
                'total_5_year_savings': annual_savings * 5 - down_payment,
                'roi_percent': ((annual_savings * 5 - down_payment) / down_payment) * 100 if down_payment > 0 else 0
            },
            'recommendation': self._get_replacement_recommendation(annual_savings, down_payment)
        }
        
        return replacement_roi
    
    def generate_cost_forecast(self, historical_data: List[Dict], forecast_months: int = 12) -> Dict:
        """Generate cost forecasts based on historical data"""
        
        # Analyze historical trends
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Calculate monthly trends
        monthly_data = df.groupby(df['date'].dt.to_period('M')).agg({
            'fuel_cost': 'sum',
            'maintenance_cost': 'sum',
            'total_cost': 'sum',
            'km_driven': 'sum',
            'fuel_used': 'sum'
        }).reset_index()
        
        # Simple trend analysis (in production, use more sophisticated forecasting)
        forecast = {
            'historical_analysis': {
                'avg_monthly_fuel_cost': monthly_data['fuel_cost'].mean(),
                'fuel_cost_trend': self._calculate_trend(monthly_data['fuel_cost'].values),
                'avg_monthly_total_cost': monthly_data['total_cost'].mean(),
                'total_cost_trend': self._calculate_trend(monthly_data['total_cost'].values)
            },
            'forecast_by_month': [],
            'forecast_summary': {}
        }
        
        # Generate monthly forecasts
        for month in range(1, forecast_months + 1):
            fuel_cost_forecast = self._project_cost(
                monthly_data['fuel_cost'].values, month, 
                seasonal_factor=self._get_seasonal_factor(month)
            )
            
            total_cost_forecast = self._project_cost(
                monthly_data['total_cost'].values, month,
                seasonal_factor=self._get_seasonal_factor(month)
            )
            
            forecast['forecast_by_month'].append({
                'month': month,
                'fuel_cost': fuel_cost_forecast,
                'total_cost': total_cost_forecast,
                'confidence_interval': self._calculate_forecast_confidence(month)
            })
        
        # Calculate forecast summary
        total_forecast_cost = sum(f['total_cost'] for f in forecast['forecast_by_month'])
        current_annual_cost = monthly_data['total_cost'].sum() * (12 / len(monthly_data))
        
        forecast['forecast_summary'] = {
            'total_forecast_cost': total_forecast_cost,
            'projected_annual_change_percent': ((total_forecast_cost - current_annual_cost) / current_annual_cost) * 100 if current_annual_cost > 0 else 0,
            'high_cost_months': [f['month'] for f in forecast['forecast_by_month'] if f['total_cost'] > forecast['historical_analysis']['avg_monthly_total_cost'] * 1.2],
            'cost_optimization_opportunities': self._identify_cost_optimization_opportunities(forecast)
        }
        
        return forecast
    
    def _calculate_npv(self, initial_investment: float, annual_savings: float, years: int, discount_rate: float) -> float:
        """Calculate Net Present Value"""
        npv = -initial_investment
        for year in range(1, years + 1):
            npv += annual_savings / ((1 + discount_rate) ** year)
        return npv
    
    def _perform_sensitivity_analysis(self, investment: float, baseline_cost: float, efficiency_improvement: float) -> Dict:
        """Perform sensitivity analysis for ROI calculations"""
        scenarios = {
            'pessimistic': efficiency_improvement * 0.5,
            'realistic': efficiency_improvement,
            'optimistic': efficiency_improvement * 1.5
        }
        
        sensitivity = {}
        for scenario, improvement in scenarios.items():
            annual_savings = baseline_cost * (improvement / 100)
            payback_months = (investment / annual_savings) * 12 if annual_savings > 0 else float('inf')
            
            sensitivity[scenario] = {
                'efficiency_improvement': improvement,
                'annual_savings': annual_savings,
                'payback_period_months': payback_months,
                'roi_percent': ((annual_savings * 3 - investment) / investment) * 100 if investment > 0 else 0
            }
        
        return sensitivity
    
    def _get_replacement_recommendation(self, annual_savings: float, down_payment: float) -> str:
        """Get recommendation for vehicle replacement"""
        if annual_savings <= 0:
            return "Not recommended: Replacement would increase annual costs"
        
        payback_months = (down_payment / annual_savings) * 12
        
        if payback_months <= 18:
            return "Highly recommended: Quick payback period"
        elif payback_months <= 36:
            return "Recommended: Reasonable payback period"
        elif payback_months <= 60:
            return "Consider: Long payback period but positive ROI"
        else:
            return "Not recommended: Payback period too long"
    
    def _calculate_trend(self, values: np.ndarray) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return 'insufficient_data'
        
        slope = np.polyfit(range(len(values)), values, 1)[0]
        
        if slope > values.mean() * 0.05:
            return 'increasing'
        elif slope < -values.mean() * 0.05:
            return 'decreasing'
        else:
            return 'stable'
    
    def _project_cost(self, historical_values: np.ndarray, months_ahead: int, seasonal_factor: float = 1.0) -> float:
        """Project future cost based on historical data"""
        if len(historical_values) < 2:
            return historical_values[-1] if len(historical_values) > 0 else 0
        
        # Simple linear projection with seasonal adjustment
        trend = np.polyfit(range(len(historical_values)), historical_values, 1)[0]
        base_value = historical_values[-1]
        projected = base_value + (trend * months_ahead)
        
        return max(0, projected * seasonal_factor)
    
    def _get_seasonal_factor(self, month: int) -> float:
        """Get seasonal factor for cost projections"""
        # Simplified seasonal factors (winter months typically higher costs)
        seasonal_factors = {
            1: 1.15, 2: 1.12, 3: 1.05, 4: 0.98, 5: 0.95, 6: 0.92,
            7: 0.90, 8: 0.92, 9: 0.95, 10: 1.02, 11: 1.08, 12: 1.15
        }
        return seasonal_factors.get(month % 12 + 1, 1.0)
    
    def _calculate_forecast_confidence(self, months_ahead: int) -> Dict:
        """Calculate confidence interval for forecasts"""
        # Confidence decreases with time
        base_confidence = max(0.6, 0.95 - (months_ahead * 0.03))
        
        return {
            'confidence_percent': base_confidence * 100,
            'margin_of_error_percent': (1 - base_confidence) * 100
        }
    
    def _identify_cost_optimization_opportunities(self, forecast: Dict) -> List[str]:
        """Identify cost optimization opportunities from forecast"""
        opportunities = []
        
        fuel_trend = forecast['historical_analysis']['fuel_cost_trend']
        if fuel_trend == 'increasing':
            opportunities.append("Consider fuel efficiency improvements due to rising fuel costs")
        
        high_cost_months = forecast['forecast_summary']['high_cost_months']
        if high_cost_months:
            opportunities.append(f"Plan preventive maintenance before high-cost months: {high_cost_months}")
        
        if forecast['forecast_summary']['projected_annual_change_percent'] > 10:
            opportunities.append("Significant cost increase projected - review operational efficiency")
        
        return opportunities

# Example usage and demonstration
if __name__ == "__main__":
    # Initialize analyzers
    cost_analyzer = CostAnalyzer()
    roi_calculator = ROICalculator()
    
    # Sample trip data
    sample_trip = {
        'fuel_used': 45.5,
        'km_driven': 320,
        'duration_hours': 6.5,
        'fuel_type': 'diesel',
        'vehicle_type': 'heavy_truck',
        'vehicle_value': 85000
    }
    
    # Calculate trip cost
    trip_cost = cost_analyzer.calculate_trip_cost(sample_trip)
    print("💰 Trip Cost Analysis:")
    print(f"   Fuel: ${trip_cost['fuel_cost']:.2f}")
    print(f"   Maintenance: ${trip_cost['maintenance_cost']:.2f}")
    print(f"   Driver: ${trip_cost['driver_cost']:.2f}")
    print(f"   Total: ${trip_cost['total_cost']:.2f}")
    print(f"   Cost per km: ${trip_cost['cost_per_km']:.2f}")
    
    # Calculate ROI for fuel optimization
    optimization_scenario = {
        'system_cost': 30000,
        'training_cost': 8000,
        'baseline': {
            'annual_fuel_cost': 180000,
            'annual_maintenance_cost': 45000
        },
        'projected': {
            'efficiency_improvement_percent': 18
        }
    }
    
    roi_analysis = roi_calculator.calculate_fuel_optimization_roi(optimization_scenario)
    print(f"\n📈 Fuel Optimization ROI:")
    print(f"   Annual savings: ${roi_analysis['annual_savings_breakdown']['total_annual_savings']:,.0f}")
    print(f"   Payback period: {roi_analysis['roi_metrics']['payback_period_months']:.1f} months")
    print(f"   Annual ROI: {roi_analysis['roi_metrics']['annual_roi_percent']:.1f}%")
    print(f"   5-year NPV: ${roi_analysis['roi_metrics']['net_present_value_5_years']:,.0f}")
    
    # Vehicle replacement analysis
    replacement_scenario = {
        'current': {
            'annual_fuel_cost': 22000,
            'annual_maintenance_cost': 12000,
            'current_value': 25000
        },
        'replacement': {
            'purchase_price': 95000,
            'down_payment': 25000,
            'annual_fuel_cost': 16000,
            'annual_maintenance_cost': 6000,
            'annual_loan_payment': 18000
        }
    }
    
    replacement_roi = roi_calculator.calculate_vehicle_replacement_roi(replacement_scenario)
    print(f"\n🚛 Vehicle Replacement ROI:")
    print(f"   Annual savings: ${replacement_roi['cost_comparison']['annual_savings']:,.0f}")
    print(f"   Payback period: {replacement_roi['investment_analysis']['payback_period_months']:.1f} months")
    print(f"   5-year ROI: {replacement_roi['investment_analysis']['roi_percent']:.1f}%")
    print(f"   Recommendation: {replacement_roi['recommendation']}")
