"""
Fuel Analysis Service
Business logic for fuel efficiency analysis and anomaly detection
"""

import pandas as pd
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add ML modules to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ml'))

try:
    from ml.isolation_model import FuelAnomalyDetector
    from ml.preprocess import FuelDataPreprocessor
except ImportError:
    # Fallback for different path structures
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'ml'))
    from isolation_model import FuelAnomalyDetector
    from preprocess import FuelDataPreprocessor
from backend.models.fuel_log import FuelLog
from backend.models.vehicle import Vehicle
from .utils import generate_summary_stats, aggregate_by_vehicle

class FuelAnalysisService:
    """
    Service for fuel efficiency analysis and anomaly detection
    """
    
    def __init__(self, db_session=None):
        """
        Initialize the fuel analysis service
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.anomaly_detector = None
        self.model_loaded = False
        self.last_training_date = None
    
    def load_or_train_model(self, retrain=False):
        """
        Load existing model or train a new one
        
        Args:
            retrain (bool): Force retraining even if model exists
            
        Returns:
            bool: Success status
        """
        model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ml', 'latest_model.pkl')
        
        try:
            # Try to load existing model if not retraining
            if not retrain and os.path.exists(model_path):
                self.anomaly_detector = FuelAnomalyDetector()
                self.anomaly_detector.load_model(model_path)
                self.model_loaded = True
                print("✅ Loaded existing anomaly detection model")
                return True
            
            # Train new model
            return self.train_new_model(model_path)
            
        except Exception as e:
            print(f"❌ Error loading/training model: {e}")
            return False
    
    def train_new_model(self, model_path=None):
        """
        Train a new anomaly detection model
        
        Args:
            model_path (str): Path to save the trained model
            
        Returns:
            bool: Success status
        """
        try:
            # Get training data from database
            training_data = self.get_fuel_data_for_training()
            
            if training_data.empty:
                print("❌ No training data available")
                return False
            
            # Initialize and train model
            self.anomaly_detector = FuelAnomalyDetector(contamination=0.05)
            training_results = self.anomaly_detector.train(
                training_data, 
                save_model=True,
                model_path=model_path
            )
            
            # Update anomaly flags in database
            self.update_anomaly_flags_in_db(training_results['processed_data'])
            
            self.model_loaded = True
            self.last_training_date = datetime.now()
            
            print("✅ Successfully trained new anomaly detection model")
            return True
            
        except Exception as e:
            print(f"❌ Error training model: {e}")
            return False
    
    def get_fuel_data_for_training(self, days_back=30):
        """
        Get fuel data from database for model training
        
        Args:
            days_back (int): Number of days to look back
            
        Returns:
            pd.DataFrame: Training data
        """
        if not self.db_session:
            raise ValueError("Database session not provided")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Query fuel logs
        fuel_logs = FuelLog.get_date_range(
            self.db_session, 
            start_date, 
            end_date
        )
        
        # Convert to DataFrame
        data = []
        for log in fuel_logs:
            data.append({
                'id': log.id,
                'vehicle_id': log.vehicle_id,
                'timestamp': log.timestamp,
                'km_driven': float(log.km_driven),
                'fuel_used': float(log.fuel_used),
                'fuel_efficiency': float(log.fuel_efficiency) if log.fuel_efficiency else 0
            })
        
        return pd.DataFrame(data)
    
    def analyze_fuel_efficiency(self, vehicle_id=None, days_back=7):
        """
        Analyze fuel efficiency for vehicles
        
        Args:
            vehicle_id (str): Specific vehicle ID (optional)
            days_back (int): Number of days to analyze
            
        Returns:
            dict: Analysis results
        """
        try:
            # Get data
            if vehicle_id:
                fuel_logs = FuelLog.get_by_vehicle(self.db_session, vehicle_id)
            else:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)
                fuel_logs = FuelLog.get_date_range(self.db_session, start_date, end_date)
            
            # Convert to DataFrame
            data = []
            for log in fuel_logs:
                data.append({
                    'vehicle_id': log.vehicle_id,
                    'timestamp': log.timestamp,
                    'km_driven': float(log.km_driven),
                    'fuel_used': float(log.fuel_used),
                    'fuel_efficiency': float(log.fuel_efficiency) if log.fuel_efficiency else 0,
                    'is_anomaly': log.is_anomaly,
                    'anomaly_score': float(log.anomaly_score) if log.anomaly_score else 0
                })
            
            df = pd.DataFrame(data)
            
            if df.empty:
                return {"status": "no_data", "message": "No fuel data available"}
            
            # Generate analysis
            analysis = {
                "summary_stats": generate_summary_stats(df),
                "vehicle_aggregates": aggregate_by_vehicle(df).to_dict('records'),
                "anomaly_summary": self.get_anomaly_summary(df),
                "efficiency_trends": self.calculate_efficiency_trends(df),
                "recommendations": self.generate_recommendations(df)
            }
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error in fuel efficiency analysis: {e}")
            return {"status": "error", "message": str(e)}
    
    def detect_anomalies(self, vehicle_id=None, update_db=True):
        """
        Detect anomalies in fuel data
        
        Args:
            vehicle_id (str): Specific vehicle ID (optional)
            update_db (bool): Whether to update database with results
            
        Returns:
            dict: Anomaly detection results
        """
        try:
            # Ensure model is loaded
            if not self.model_loaded:
                if not self.load_or_train_model():
                    return {"status": "error", "message": "Could not load anomaly detection model"}
            
            # Get recent data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)  # Last week
            
            if vehicle_id:
                fuel_logs = FuelLog.get_by_vehicle(self.db_session, vehicle_id)
                fuel_logs = [log for log in fuel_logs if start_date <= log.timestamp <= end_date]
            else:
                fuel_logs = FuelLog.get_date_range(self.db_session, start_date, end_date)
            
            # Convert to DataFrame
            data = []
            for log in fuel_logs:
                data.append({
                    'id': log.id,
                    'vehicle_id': log.vehicle_id,
                    'timestamp': log.timestamp,
                    'km_driven': float(log.km_driven),
                    'fuel_used': float(log.fuel_used),
                    'fuel_efficiency': float(log.fuel_efficiency) if log.fuel_efficiency else 0
                })
            
            df = pd.DataFrame(data)
            
            if df.empty:
                return {"status": "no_data", "message": "No recent fuel data available"}
            
            # Run anomaly detection
            df_with_anomalies = self.anomaly_detector.predict(df)
            
            # Update database if requested
            if update_db:
                self.update_anomaly_flags_in_db(df_with_anomalies)
            
            # Get anomalies
            anomalies = self.anomaly_detector.get_anomalies(df_with_anomalies)
            
            # Generate results
            results = {
                "status": "success",
                "total_records": len(df_with_anomalies),
                "anomalies_detected": len(anomalies),
                "anomaly_rate": len(anomalies) / len(df_with_anomalies) if len(df_with_anomalies) > 0 else 0,
                "anomalies": anomalies.to_dict('records') if not anomalies.empty else [],
                "top_anomalies": self.anomaly_detector.get_top_anomalies(df_with_anomalies, 5).to_dict('records'),
                "vehicle_analysis": self.anomaly_detector.analyze_anomalies_by_vehicle(df_with_anomalies).to_dict('records')
            }
            
            return results
            
        except Exception as e:
            print(f"❌ Error in anomaly detection: {e}")
            return {"status": "error", "message": str(e)}
    
    def update_anomaly_flags_in_db(self, df_with_predictions):
        """
        Update anomaly flags in the database
        
        Args:
            df_with_predictions (pd.DataFrame): Data with anomaly predictions
        """
        try:
            for _, row in df_with_predictions.iterrows():
                if 'id' in row and pd.notna(row['id']):
                    fuel_log = self.db_session.query(FuelLog).filter(
                        FuelLog.id == int(row['id'])
                    ).first()
                    
                    if fuel_log:
                        fuel_log.is_anomaly = bool(row.get('is_anomaly_predicted', False))
                        fuel_log.anomaly_score = float(row.get('anomaly_score', 0))
            
            self.db_session.commit()
            print(f"✅ Updated anomaly flags for {len(df_with_predictions)} records")
            
        except Exception as e:
            print(f"❌ Error updating anomaly flags: {e}")
            self.db_session.rollback()
    
    def get_anomaly_summary(self, df):
        """
        Generate anomaly summary statistics
        
        Args:
            df (pd.DataFrame): Fuel data with anomaly flags
            
        Returns:
            dict: Anomaly summary
        """
        total_records = len(df)
        anomalies = df[df.get('is_anomaly', False) == True]
        
        summary = {
            "total_records": total_records,
            "anomalies_detected": len(anomalies),
            "anomaly_rate": len(anomalies) / total_records if total_records > 0 else 0,
            "avg_anomaly_score": float(df.get('anomaly_score', pd.Series([0])).mean()),
            "vehicles_with_anomalies": anomalies['vehicle_id'].nunique() if not anomalies.empty else 0
        }
        
        return summary
    
    def calculate_efficiency_trends(self, df):
        """
        Calculate fuel efficiency trends over time
        
        Args:
            df (pd.DataFrame): Fuel data
            
        Returns:
            dict: Efficiency trends
        """
        try:
            # Group by date and calculate daily averages
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            daily_efficiency = df.groupby('date')['fuel_efficiency'].mean()
            
            # Calculate trend
            if len(daily_efficiency) > 1:
                x = range(len(daily_efficiency))
                y = daily_efficiency.values
                trend_slope = pd.Series(y).corr(pd.Series(x))
                
                trend_direction = "improving" if trend_slope > 0.1 else "declining" if trend_slope < -0.1 else "stable"
            else:
                trend_slope = 0
                trend_direction = "insufficient_data"
            
            trends = {
                "trend_direction": trend_direction,
                "trend_slope": float(trend_slope),
                "daily_averages": [
                    {"date": str(date), "efficiency": float(eff)} 
                    for date, eff in daily_efficiency.items()
                ],
                "best_day": {
                    "date": str(daily_efficiency.idxmax()),
                    "efficiency": float(daily_efficiency.max())
                } if not daily_efficiency.empty else None,
                "worst_day": {
                    "date": str(daily_efficiency.idxmin()),
                    "efficiency": float(daily_efficiency.min())
                } if not daily_efficiency.empty else None
            }
            
            return trends
            
        except Exception as e:
            print(f"❌ Error calculating efficiency trends: {e}")
            return {"trend_direction": "error", "message": str(e)}
    
    def generate_recommendations(self, df):
        """
        Generate actionable recommendations based on analysis
        
        Args:
            df (pd.DataFrame): Fuel data
            
        Returns:
            list: List of recommendations
        """
        recommendations = []
        
        try:
            # Check for vehicles with consistently poor efficiency
            vehicle_efficiency = df.groupby('vehicle_id')['fuel_efficiency'].mean()
            fleet_average = vehicle_efficiency.mean()
            
            poor_performers = vehicle_efficiency[vehicle_efficiency < fleet_average * 0.8]
            
            for vehicle_id, efficiency in poor_performers.items():
                recommendations.append({
                    "type": "efficiency_concern",
                    "priority": "high",
                    "vehicle_id": vehicle_id,
                    "message": f"Vehicle {vehicle_id} has poor fuel efficiency ({efficiency:.2f} km/L vs fleet average {fleet_average:.2f} km/L)",
                    "action": "Schedule maintenance check for engine and fuel system"
                })
            
            # Check for vehicles with high anomaly rates
            anomaly_rates = df.groupby('vehicle_id')['is_anomaly'].mean()
            high_anomaly_vehicles = anomaly_rates[anomaly_rates > 0.2]  # > 20% anomaly rate
            
            for vehicle_id, rate in high_anomaly_vehicles.items():
                recommendations.append({
                    "type": "anomaly_concern",
                    "priority": "medium",
                    "vehicle_id": vehicle_id,
                    "message": f"Vehicle {vehicle_id} has high anomaly rate ({rate:.1%})",
                    "action": "Review driving patterns and route efficiency"
                })
            
            # Check for overall fleet efficiency
            if fleet_average < 8.0:  # Assuming 8 km/L as reasonable efficiency
                recommendations.append({
                    "type": "fleet_efficiency",
                    "priority": "medium",
                    "message": f"Fleet average efficiency is low ({fleet_average:.2f} km/L)",
                    "action": "Consider driver training programs and vehicle maintenance review"
                })
            
            # Recent trend analysis
            recent_data = df.tail(20)  # Last 20 records
            if not recent_data.empty:
                recent_avg = recent_data['fuel_efficiency'].mean()
                overall_avg = df['fuel_efficiency'].mean()
                
                if recent_avg < overall_avg * 0.9:
                    recommendations.append({
                        "type": "declining_trend",
                        "priority": "high",
                        "message": f"Recent efficiency decline detected ({recent_avg:.2f} vs {overall_avg:.2f} km/L)",
                        "action": "Investigate recent changes in routes, drivers, or vehicle conditions"
                    })
            
        except Exception as e:
            print(f"❌ Error generating recommendations: {e}")
            recommendations.append({
                "type": "error",
                "priority": "low",
                "message": f"Could not generate some recommendations: {str(e)}"
            })
        
        return recommendations
    
    def get_model_status(self):
        """
        Get current model status and information
        
        Returns:
            dict: Model status information
        """
        if not self.anomaly_detector:
            return {"status": "not_initialized"}
        
        model_info = self.anomaly_detector.get_model_info()
        model_info["last_training_date"] = self.last_training_date.isoformat() if self.last_training_date else None
        model_info["model_loaded"] = self.model_loaded
        
        return model_info
