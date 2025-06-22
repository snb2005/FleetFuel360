"""
Isolation Forest Anomaly Detection Model
Train and predict fuel efficiency anomalies
"""

import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# Import preprocessor - handle both relative and absolute imports
try:
    from .preprocess import FuelDataPreprocessor
except ImportError:
    from preprocess import FuelDataPreprocessor

class FuelAnomalyDetector:
    """
    Isolation Forest-based anomaly detector for fuel efficiency data
    """
    
    def __init__(self, contamination=0.05, random_state=42):
        """
        Initialize the anomaly detector
        
        Args:
            contamination (float): Expected proportion of anomalies (default: 0.05 = 5%)
            random_state (int): Random seed for reproducibility
        """
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
            max_samples='auto',
            max_features=1.0,
            bootstrap=False,
            n_jobs=-1
        )
        self.preprocessor = FuelDataPreprocessor()
        self.is_trained = False
        self.model_version = None
        self.training_stats = {}
    
    def train(self, df, save_model=True, model_path=None):
        """
        Train the anomaly detection model
        
        Args:
            df (pd.DataFrame): Training data with fuel logs
            save_model (bool): Whether to save the trained model
            model_path (str): Path to save the model
            
        Returns:
            dict: Training results and statistics
        """
        print("🤖 Training Isolation Forest model...")
        
        # Preprocess the data
        df_processed, ml_features, original_indices = self.preprocessor.fit_transform(df)
        
        if len(ml_features) == 0:
            raise ValueError("No valid data available for training")
        
        # Train the model
        self.model.fit(ml_features)
        
        # Predict anomalies on training data
        anomaly_scores = self.model.decision_function(ml_features)
        anomaly_predictions = self.model.predict(ml_features)
        
        # Convert predictions (-1 for anomalies, 1 for normal) to boolean
        is_anomaly = anomaly_predictions == -1
        
        # Store results back to processed dataframe
        df_processed['anomaly_score'] = anomaly_scores
        df_processed['is_anomaly_predicted'] = is_anomaly
        
        # Calculate training statistics
        total_records = len(df_processed)
        anomalies_detected = is_anomaly.sum()
        anomaly_rate = anomalies_detected / total_records
        
        self.training_stats = {
            'total_records': total_records,
            'anomalies_detected': anomalies_detected,
            'anomaly_rate': anomaly_rate,
            'features_used': len(self.preprocessor.feature_columns),
            'feature_names': self.preprocessor.feature_columns,
            'contamination_setting': self.contamination,
            'training_date': datetime.now().isoformat()
        }
        
        self.is_trained = True
        self.model_version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save model if requested
        if save_model:
            if model_path is None:
                model_path = os.path.join(os.path.dirname(__file__), f'anomaly_model_{self.model_version}.pkl')
            self.save_model(model_path)
        
        print(f"✅ Training completed:")
        print(f"   - Total records: {total_records}")
        print(f"   - Anomalies detected: {anomalies_detected} ({anomaly_rate:.2%})")
        print(f"   - Features used: {len(self.preprocessor.feature_columns)}")
        
        return {
            'processed_data': df_processed,
            'training_stats': self.training_stats,
            'model_version': self.model_version
        }
    
    def predict(self, df):
        """
        Predict anomalies on new data
        
        Args:
            df (pd.DataFrame): New fuel log data
            
        Returns:
            pd.DataFrame: Data with anomaly predictions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Preprocess the data
        df_processed, ml_features, original_indices = self.preprocessor.transform(df)
        
        if len(ml_features) == 0:
            print("⚠️ No valid data available for prediction")
            return df_processed
        
        # Make predictions
        anomaly_scores = self.model.decision_function(ml_features)
        anomaly_predictions = self.model.predict(ml_features)
        
        # Convert predictions (-1 for anomalies, 1 for normal) to boolean
        is_anomaly = anomaly_predictions == -1
        
        # Store results
        df_processed['anomaly_score'] = anomaly_scores
        df_processed['is_anomaly_predicted'] = is_anomaly
        
        return df_processed
    
    def get_anomalies(self, df, threshold=None):
        """
        Get records flagged as anomalies
        
        Args:
            df (pd.DataFrame): Data with predictions
            threshold (float): Custom anomaly score threshold
            
        Returns:
            pd.DataFrame: Anomalous records only
        """
        if 'is_anomaly_predicted' not in df.columns:
            df = self.predict(df)
        
        if threshold is not None:
            # Use custom threshold on anomaly scores
            anomalies = df[df['anomaly_score'] < threshold].copy()
        else:
            # Use model predictions
            anomalies = df[df['is_anomaly_predicted'] == True].copy()
        
        return anomalies.sort_values('anomaly_score')
    
    def get_top_anomalies(self, df, n=10):
        """
        Get top N most anomalous records
        
        Args:
            df (pd.DataFrame): Data with predictions
            n (int): Number of top anomalies to return
            
        Returns:
            pd.DataFrame: Top N anomalous records
        """
        if 'anomaly_score' not in df.columns:
            df = self.predict(df)
        
        return df.nsmallest(n, 'anomaly_score')
    
    def analyze_anomalies_by_vehicle(self, df):
        """
        Analyze anomalies grouped by vehicle
        
        Args:
            df (pd.DataFrame): Data with predictions
            
        Returns:
            pd.DataFrame: Anomaly analysis by vehicle
        """
        if 'is_anomaly_predicted' not in df.columns:
            df = self.predict(df)
        
        analysis = df.groupby('vehicle_id').agg({
            'is_anomaly_predicted': ['count', 'sum'],
            'anomaly_score': ['mean', 'min'],
            'fuel_efficiency': ['mean', 'std'],
            'fuel_used': 'mean',
            'km_driven': 'mean'
        }).round(4)
        
        # Flatten column names
        analysis.columns = ['_'.join(col).strip() for col in analysis.columns]
        analysis = analysis.reset_index()
        
        # Calculate anomaly rate
        analysis['anomaly_rate'] = (
            analysis['is_anomaly_predicted_sum'] / analysis['is_anomaly_predicted_count']
        )
        
        # Rename columns for clarity
        column_mapping = {
            'is_anomaly_predicted_count': 'total_records',
            'is_anomaly_predicted_sum': 'anomalies_detected',
            'anomaly_score_mean': 'avg_anomaly_score',
            'anomaly_score_min': 'worst_anomaly_score',
            'fuel_efficiency_mean': 'avg_fuel_efficiency',
            'fuel_efficiency_std': 'fuel_efficiency_std',
            'fuel_used_mean': 'avg_fuel_used',
            'km_driven_mean': 'avg_km_driven'
        }
        
        analysis = analysis.rename(columns=column_mapping)
        
        return analysis.sort_values('anomaly_rate', ascending=False)
    
    def get_model_info(self):
        """
        Get information about the trained model
        
        Returns:
            dict: Model information and statistics
        """
        if not self.is_trained:
            return {"status": "not_trained"}
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy_types(obj):
            if hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj
        
        return {
            "status": "trained",
            "model_version": self.model_version,
            "contamination": float(self.contamination),
            "training_stats": convert_numpy_types(self.training_stats),
            "model_params": convert_numpy_types(self.model.get_params()),
            "preprocessor_features": list(self.preprocessor.feature_columns)
        }
    
    def save_model(self, filepath):
        """
        Save the trained model and preprocessor
        
        Args:
            filepath (str): Path to save the model
        """
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        model_data = {
            'model': self.model,
            'preprocessor': self.preprocessor,
            'model_version': self.model_version,
            'training_stats': self.training_stats,
            'contamination': self.contamination,
            'random_state': self.random_state
        }
        
        joblib.dump(model_data, filepath)
        print(f"✅ Model saved to: {filepath}")
    
    def load_model(self, filepath):
        """
        Load a previously trained model
        
        Args:
            filepath (str): Path to the saved model
        """
        try:
            model_data = joblib.load(filepath)
            
            self.model = model_data['model']
            self.preprocessor = model_data['preprocessor']
            self.model_version = model_data.get('model_version', 'unknown')
            self.training_stats = model_data.get('training_stats', {})
            self.contamination = model_data.get('contamination', 0.05)
            self.random_state = model_data.get('random_state', 42)
            self.is_trained = True
            
            print(f"✅ Model loaded from: {filepath}")
            print(f"   Version: {self.model_version}")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise
    
    def evaluate_with_labels(self, df, true_anomaly_column):
        """
        Evaluate model performance if true labels are available
        
        Args:
            df (pd.DataFrame): Data with true anomaly labels
            true_anomaly_column (str): Name of the column with true labels
            
        Returns:
            dict: Evaluation metrics
        """
        if true_anomaly_column not in df.columns:
            raise ValueError(f"Column {true_anomaly_column} not found in data")
        
        # Get predictions
        df_predicted = self.predict(df)
        
        # Get true and predicted labels
        y_true = df_predicted[true_anomaly_column].astype(bool)
        y_pred = df_predicted['is_anomaly_predicted'].astype(bool)
        
        # Calculate metrics
        from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
        
        evaluation = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1_score': f1_score(y_true, y_pred, zero_division=0),
            'confusion_matrix': confusion_matrix(y_true, y_pred).tolist(),
            'classification_report': classification_report(y_true, y_pred, zero_division=0)
        }
        
        return evaluation
