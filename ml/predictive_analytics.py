"""
Advanced Predictive Analytics for FleetFuel360
Implements multiple ML models for different prediction tasks
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import warnings
warnings.filterwarnings('ignore')

class PredictiveAnalytics:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_columns = {}
        self.model_metrics = {}
        
    def prepare_features(self, df):
        """Prepare features for predictive modeling"""
        # Create a copy to avoid modifying original data
        data = df.copy()
        
        # Ensure timestamp is datetime
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        
        # Time-based features
        data['hour'] = data['timestamp'].dt.hour
        data['day_of_week'] = data['timestamp'].dt.dayofweek
        data['month'] = data['timestamp'].dt.month
        data['is_weekend'] = data['day_of_week'].isin([5, 6]).astype(int)
        data['is_peak_hour'] = data['hour'].isin([7, 8, 9, 17, 18, 19]).astype(int)
        
        # Vehicle-specific features
        for vehicle_id in data['vehicle_id'].unique():
            vehicle_data = data[data['vehicle_id'] == vehicle_id].copy()
            
            # Rolling averages (last 5 trips)
            vehicle_data['efficiency_ma5'] = vehicle_data['fuel_efficiency'].rolling(5).mean()
            vehicle_data['km_ma5'] = vehicle_data['km_driven'].rolling(5).mean()
            vehicle_data['fuel_ma5'] = vehicle_data['fuel_used'].rolling(5).mean()
            
            # Efficiency trends
            vehicle_data['efficiency_trend'] = vehicle_data['fuel_efficiency'].diff()
            vehicle_data['efficiency_volatility'] = vehicle_data['fuel_efficiency'].rolling(5).std()
            
            # Trip characteristics
            vehicle_data['trip_duration_est'] = vehicle_data['km_driven'] / 50  # Assuming avg 50 km/h
            vehicle_data['fuel_intensity'] = vehicle_data['fuel_used'] / vehicle_data['km_driven']
            
            # Update main dataframe
            data.loc[data['vehicle_id'] == vehicle_id, vehicle_data.columns] = vehicle_data
        
        # Forward fill missing values
        data = data.fillna(method='ffill').fillna(method='bfill')
        
        return data
    
    def train_fuel_consumption_predictor(self, df):
        """Train model to predict fuel consumption"""
        print("🤖 Training Fuel Consumption Predictor...")
        
        # Prepare features
        data = self.prepare_features(df)
        
        # Feature selection for fuel consumption prediction
        feature_cols = [
            'km_driven', 'hour', 'day_of_week', 'month', 'is_weekend', 'is_peak_hour',
            'efficiency_ma5', 'km_ma5', 'efficiency_trend', 'efficiency_volatility',
            'trip_duration_est'
        ]
        
        # Remove rows with missing values
        clean_data = data.dropna(subset=feature_cols + ['fuel_used'])
        
        if len(clean_data) < 10:
            print("❌ Insufficient data for training")
            return False
        
        X = clean_data[feature_cols]
        y = clean_data['fuel_used']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train multiple models and select best
        models_to_try = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(random_state=42),
            'linear_regression': LinearRegression()
        }
        
        best_model = None
        best_score = -np.inf
        
        for name, model in models_to_try.items():
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
            score = r2_score(y_test, y_pred)
            
            if score > best_score:
                best_score = score
                best_model = model
                best_model_name = name
        
        # Store model and scaler
        self.models['fuel_consumption'] = best_model
        self.scalers['fuel_consumption'] = scaler
        self.feature_columns['fuel_consumption'] = feature_cols
        
        # Calculate metrics
        y_pred = best_model.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        self.model_metrics['fuel_consumption'] = {
            'model_type': best_model_name,
            'r2_score': r2,
            'mae': mae,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'feature_importance': self._get_feature_importance(best_model, feature_cols)
        }
        
        print(f"✅ Fuel consumption predictor trained ({best_model_name})")
        print(f"   R² Score: {r2:.3f}, MAE: {mae:.2f}L")
        
        return True
    
    def train_maintenance_predictor(self, df):
        """Train model to predict maintenance needs"""
        print("🔧 Training Maintenance Predictor...")
        
        # Prepare features
        data = self.prepare_features(df)
        
        # Simulate maintenance data (in real world, this would come from maintenance records)
        data['cumulative_km'] = data.groupby('vehicle_id')['km_driven'].cumsum()
        data['trips_since_maintenance'] = data.groupby('vehicle_id').cumcount()
        data['maintenance_due'] = ((data['cumulative_km'] % 5000) > 4500).astype(int)
        
        feature_cols = [
            'cumulative_km', 'trips_since_maintenance', 'efficiency_volatility',
            'fuel_intensity', 'efficiency_trend'
        ]
        
        clean_data = data.dropna(subset=feature_cols + ['maintenance_due'])
        
        if len(clean_data) < 10:
            print("❌ Insufficient data for maintenance prediction")
            return False
        
        X = clean_data[feature_cols]
        y = clean_data['maintenance_due']
        
        # Train classifier
        from sklearn.ensemble import RandomForestClassifier
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train_scaled, y_train)
        
        # Store model
        self.models['maintenance'] = model
        self.scalers['maintenance'] = scaler
        self.feature_columns['maintenance'] = feature_cols
        
        # Calculate metrics
        from sklearn.metrics import accuracy_score, classification_report
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.model_metrics['maintenance'] = {
            'model_type': 'random_forest_classifier',
            'accuracy': accuracy,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'feature_importance': self._get_feature_importance(model, feature_cols)
        }
        
        print(f"✅ Maintenance predictor trained")
        print(f"   Accuracy: {accuracy:.3f}")
        
        return True
    
    def predict_fuel_consumption(self, trip_data):
        """Predict fuel consumption for a trip"""
        if 'fuel_consumption' not in self.models:
            return None, "Fuel consumption model not trained"
        
        try:
            # Prepare features
            features = self._prepare_prediction_features(trip_data, 'fuel_consumption')
            
            # Scale features
            features_scaled = self.scalers['fuel_consumption'].transform([features])
            
            # Make prediction
            prediction = self.models['fuel_consumption'].predict(features_scaled)[0]
            
            # Calculate confidence interval (approximate)
            confidence = self._calculate_prediction_confidence('fuel_consumption', features_scaled)
            
            return {
                'predicted_fuel_consumption': prediction,
                'confidence_interval': confidence,
                'model_accuracy': self.model_metrics['fuel_consumption']['r2_score']
            }, None
            
        except Exception as e:
            return None, f"Prediction error: {str(e)}"
    
    def predict_maintenance_probability(self, vehicle_data):
        """Predict probability of maintenance being needed"""
        if 'maintenance' not in self.models:
            return None, "Maintenance model not trained"
        
        try:
            # Prepare features
            features = self._prepare_prediction_features(vehicle_data, 'maintenance')
            
            # Scale features
            features_scaled = self.scalers['maintenance'].transform([features])
            
            # Make prediction
            probability = self.models['maintenance'].predict_proba(features_scaled)[0][1]
            
            return {
                'maintenance_probability': probability,
                'recommendation': self._get_maintenance_recommendation(probability),
                'model_accuracy': self.model_metrics['maintenance']['accuracy']
            }, None
            
        except Exception as e:
            return None, f"Prediction error: {str(e)}"
    
    def forecast_fleet_efficiency(self, df, days_ahead=30):
        """Forecast fleet-wide efficiency trends"""
        print(f"📈 Forecasting fleet efficiency for next {days_ahead} days...")
        
        # Prepare time series data
        daily_efficiency = df.groupby([
            df['timestamp'].dt.date, 'vehicle_id'
        ])['fuel_efficiency'].mean().reset_index()
        
        daily_efficiency['timestamp'] = pd.to_datetime(daily_efficiency['timestamp'])
        
        # Simple trend analysis (in production, use ARIMA or Prophet)
        forecasts = {}
        
        for vehicle_id in daily_efficiency['vehicle_id'].unique():
            vehicle_data = daily_efficiency[daily_efficiency['vehicle_id'] == vehicle_id].copy()
            vehicle_data = vehicle_data.sort_values('timestamp')
            
            if len(vehicle_data) < 5:
                continue
            
            # Simple linear trend
            X = np.arange(len(vehicle_data)).reshape(-1, 1)
            y = vehicle_data['fuel_efficiency'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Forecast future points
            future_X = np.arange(len(vehicle_data), len(vehicle_data) + days_ahead).reshape(-1, 1)
            future_y = model.predict(future_X)
            
            # Create future dates
            last_date = vehicle_data['timestamp'].max()
            future_dates = [last_date + timedelta(days=i+1) for i in range(days_ahead)]
            
            forecasts[vehicle_id] = {
                'dates': future_dates,
                'efficiency_forecast': future_y.tolist(),
                'trend_slope': model.coef_[0],
                'current_efficiency': vehicle_data['fuel_efficiency'].iloc[-1],
                'forecast_change': future_y[-1] - vehicle_data['fuel_efficiency'].iloc[-1]
            }
        
        return forecasts
    
    def _prepare_prediction_features(self, data, model_type):
        """Prepare features for prediction"""
        feature_cols = self.feature_columns[model_type]
        features = []
        
        for col in feature_cols:
            if col in data:
                features.append(data[col])
            else:
                # Provide default values for missing features
                features.append(0)
        
        return features
    
    def _get_feature_importance(self, model, feature_cols):
        """Get feature importance from model"""
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
            return dict(zip(feature_cols, importance))
        return {}
    
    def _calculate_prediction_confidence(self, model_type, features):
        """Calculate prediction confidence interval"""
        # Simplified confidence calculation
        mae = self.model_metrics[model_type].get('mae', 1.0)
        return {
            'lower_bound': -mae,
            'upper_bound': mae
        }
    
    def _get_maintenance_recommendation(self, probability):
        """Get maintenance recommendation based on probability"""
        if probability > 0.8:
            return "URGENT: Schedule maintenance immediately"
        elif probability > 0.6:
            return "Schedule maintenance within 1 week"
        elif probability > 0.4:
            return "Monitor closely, consider scheduling maintenance"
        else:
            return "No immediate maintenance required"
    
    def save_models(self, filepath_prefix='ml/predictive_models'):
        """Save trained models"""
        try:
            for model_name, model in self.models.items():
                joblib.dump(model, f'{filepath_prefix}_{model_name}_model.pkl')
                joblib.dump(self.scalers[model_name], f'{filepath_prefix}_{model_name}_scaler.pkl')
            
            # Save metadata
            import json
            with open(f'{filepath_prefix}_metadata.json', 'w') as f:
                json.dump({
                    'feature_columns': self.feature_columns,
                    'model_metrics': self.model_metrics,
                    'training_date': datetime.now().isoformat()
                }, f, indent=2)
            
            print("✅ Predictive models saved successfully")
            return True
        except Exception as e:
            print(f"❌ Error saving models: {e}")
            return False
    
    def load_models(self, filepath_prefix='ml/predictive_models'):
        """Load trained models"""
        try:
            import json
            import os
            
            # Load metadata
            metadata_file = f'{filepath_prefix}_metadata.json'
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                self.feature_columns = metadata['feature_columns']
                self.model_metrics = metadata['model_metrics']
            
            # Load models
            for model_name in self.feature_columns.keys():
                model_file = f'{filepath_prefix}_{model_name}_model.pkl'
                scaler_file = f'{filepath_prefix}_{model_name}_scaler.pkl'
                
                if os.path.exists(model_file) and os.path.exists(scaler_file):
                    self.models[model_name] = joblib.load(model_file)
                    self.scalers[model_name] = joblib.load(scaler_file)
            
            print(f"✅ Loaded {len(self.models)} predictive models")
            return True
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False

# Example usage
if __name__ == "__main__":
    # Create sample data for testing
    np.random.seed(42)
    dates = pd.date_range('2025-01-01', '2025-06-22', freq='D')
    
    sample_data = []
    for date in dates:
        for vehicle in ['TRUCK001', 'TRUCK002', 'TRUCK003']:
            # Simulate realistic data with trends
            base_efficiency = 7.5 + np.random.normal(0, 0.5)
            fuel_used = np.random.uniform(10, 25)
            km_driven = fuel_used * base_efficiency + np.random.normal(0, 5)
            
            sample_data.append({
                'vehicle_id': vehicle,
                'timestamp': date,
                'fuel_used': fuel_used,
                'km_driven': km_driven,
                'fuel_efficiency': km_driven / fuel_used if fuel_used > 0 else 0
            })
    
    df = pd.DataFrame(sample_data)
    
    # Initialize and train predictive analytics
    predictor = PredictiveAnalytics()
    
    # Train models
    predictor.train_fuel_consumption_predictor(df)
    predictor.train_maintenance_predictor(df)
    
    # Make predictions
    test_trip = {
        'km_driven': 150,
        'hour': 8,
        'day_of_week': 1,
        'month': 6,
        'is_weekend': 0,
        'is_peak_hour': 1
    }
    
    fuel_prediction, error = predictor.predict_fuel_consumption(test_trip)
    if fuel_prediction:
        print(f"\n🔮 Fuel Prediction: {fuel_prediction['predicted_fuel_consumption']:.2f}L")
        print(f"   Model R²: {fuel_prediction['model_accuracy']:.3f}")
    
    # Fleet forecast
    forecasts = predictor.forecast_fleet_efficiency(df, days_ahead=7)
    print(f"\n📊 Generated forecasts for {len(forecasts)} vehicles")
    
    # Save models
    predictor.save_models()
