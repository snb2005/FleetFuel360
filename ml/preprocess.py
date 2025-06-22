"""
Data Preprocessing Module
Clean and engineer features for anomaly detection
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class FuelDataPreprocessor:
    """
    Preprocessor for fuel efficiency data
    Handles cleaning, feature engineering, and scaling
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.is_fitted = False
    
    def clean_data(self, df):
        """
        Clean raw fuel data
        
        Args:
            df (pd.DataFrame): Raw fuel data
            
        Returns:
            pd.DataFrame: Cleaned data
        """
        # Create a copy to avoid modifying original
        df_cleaned = df.copy()
        
        # Remove records with invalid fuel or km values
        df_cleaned = df_cleaned[
            (df_cleaned['fuel_used'] > 0) & 
            (df_cleaned['km_driven'] > 0)
        ]
        
        # Calculate fuel efficiency if not present
        if 'fuel_efficiency' not in df_cleaned.columns:
            df_cleaned['fuel_efficiency'] = df_cleaned['km_driven'] / df_cleaned['fuel_used']
        
        # Remove extreme outliers (beyond 3 standard deviations)
        for col in ['fuel_used', 'km_driven', 'fuel_efficiency']:
            if col in df_cleaned.columns:
                mean_val = df_cleaned[col].mean()
                std_val = df_cleaned[col].std()
                df_cleaned = df_cleaned[
                    abs(df_cleaned[col] - mean_val) <= (3 * std_val)
                ]
        
        # Sort by timestamp
        if 'timestamp' in df_cleaned.columns:
            df_cleaned = df_cleaned.sort_values('timestamp')
        
        return df_cleaned.reset_index(drop=True)
    
    def engineer_features(self, df):
        """
        Engineer features for anomaly detection
        
        Args:
            df (pd.DataFrame): Cleaned fuel data
            
        Returns:
            pd.DataFrame: Data with engineered features
        """
        df_features = df.copy()
        
        # Convert timestamp to datetime if string
        if 'timestamp' in df_features.columns:
            if df_features['timestamp'].dtype == 'object':
                df_features['timestamp'] = pd.to_datetime(df_features['timestamp'])
        
        # Time-based features
        if 'timestamp' in df_features.columns:
            df_features['hour'] = df_features['timestamp'].dt.hour
            df_features['day_of_week'] = df_features['timestamp'].dt.dayofweek
            df_features['is_weekend'] = (df_features['day_of_week'] >= 5).astype(int)
        
        # Vehicle-specific features (grouped by vehicle_id)
        vehicle_stats = df_features.groupby('vehicle_id').agg({
            'fuel_efficiency': ['mean', 'std', 'min', 'max'],
            'fuel_used': ['mean', 'std'],
            'km_driven': ['mean', 'std']
        }).round(4)
        
        # Flatten column names
        vehicle_stats.columns = ['_'.join(col).strip() for col in vehicle_stats.columns]
        vehicle_stats = vehicle_stats.reset_index()
        
        # Merge vehicle statistics back to main dataframe
        df_features = df_features.merge(vehicle_stats, on='vehicle_id', how='left')
        
        # Calculate deviation from vehicle average
        df_features['efficiency_deviation'] = (
            df_features['fuel_efficiency'] - df_features['fuel_efficiency_mean']
        ) / df_features['fuel_efficiency_std'].replace(0, 1)
        
        df_features['fuel_used_deviation'] = (
            df_features['fuel_used'] - df_features['fuel_used_mean']
        ) / df_features['fuel_used_std'].replace(0, 1)
        
        df_features['km_driven_deviation'] = (
            df_features['km_driven'] - df_features['km_driven_mean']
        ) / df_features['km_driven_std'].replace(0, 1)
        
        # Rolling statistics (3-record window per vehicle)
        df_features = df_features.sort_values(['vehicle_id', 'timestamp'])
        
        for col in ['fuel_efficiency', 'fuel_used', 'km_driven']:
            df_features[f'{col}_rolling_mean'] = (
                df_features.groupby('vehicle_id')[col]
                .rolling(window=3, min_periods=1)
                .mean()
                .reset_index(0, drop=True)
            )
            
            df_features[f'{col}_rolling_std'] = (
                df_features.groupby('vehicle_id')[col]
                .rolling(window=3, min_periods=1)
                .std()
                .fillna(0)
                .reset_index(0, drop=True)
            )
        
        # Distance and fuel consumption ratios
        df_features['fuel_per_km'] = df_features['fuel_used'] / df_features['km_driven']
        
        # Fill any remaining NaN values
        numeric_columns = df_features.select_dtypes(include=[np.number]).columns
        df_features[numeric_columns] = df_features[numeric_columns].fillna(0)
        
        return df_features
    
    def select_features_for_ml(self, df):
        """
        Select relevant features for machine learning
        
        Args:
            df (pd.DataFrame): DataFrame with engineered features
            
        Returns:
            pd.DataFrame: DataFrame with selected features only
        """
        # Features to use for anomaly detection
        ml_features = [
            'fuel_efficiency',
            'fuel_used',
            'km_driven',
            'hour',
            'day_of_week',
            'is_weekend',
            'efficiency_deviation',
            'fuel_used_deviation',
            'km_driven_deviation',
            'fuel_efficiency_rolling_mean',
            'fuel_efficiency_rolling_std',
            'fuel_used_rolling_mean',
            'fuel_used_rolling_std',
            'km_driven_rolling_mean',
            'km_driven_rolling_std',
            'fuel_per_km'
        ]
        
        # Filter to only include existing columns
        available_features = [col for col in ml_features if col in df.columns]
        
        self.feature_columns = available_features
        return df[available_features].copy()
    
    def fit_transform(self, df):
        """
        Fit the preprocessor and transform the data
        
        Args:
            df (pd.DataFrame): Raw fuel data
            
        Returns:
            tuple: (processed_df, ml_features_df, original_indices)
        """
        # Clean the data
        df_cleaned = self.clean_data(df)
        
        # Engineer features
        df_features = self.engineer_features(df_cleaned)
        
        # Select ML features
        ml_features = self.select_features_for_ml(df_features)
        
        # Fit and transform the scaler
        ml_features_scaled = pd.DataFrame(
            self.scaler.fit_transform(ml_features),
            columns=ml_features.columns,
            index=ml_features.index
        )
        
        self.is_fitted = True
        
        return df_features, ml_features_scaled, df_cleaned.index
    
    def transform(self, df):
        """
        Transform new data using fitted preprocessor
        
        Args:
            df (pd.DataFrame): Raw fuel data
            
        Returns:
            tuple: (processed_df, ml_features_df, original_indices)
        """
        if not self.is_fitted:
            raise ValueError("Preprocessor must be fitted before transform")
        
        # Clean the data
        df_cleaned = self.clean_data(df)
        
        # Engineer features
        df_features = self.engineer_features(df_cleaned)
        
        # Select ML features
        ml_features = self.select_features_for_ml(df_features)
        
        # Ensure all required columns are present
        for col in self.feature_columns:
            if col not in ml_features.columns:
                ml_features[col] = 0
        
        # Reorder columns to match training data
        ml_features = ml_features[self.feature_columns]
        
        # Transform using fitted scaler
        ml_features_scaled = pd.DataFrame(
            self.scaler.transform(ml_features),
            columns=ml_features.columns,
            index=ml_features.index
        )
        
        return df_features, ml_features_scaled, df_cleaned.index
    
    def get_feature_importance_data(self, df):
        """
        Get data for feature importance analysis
        
        Args:
            df (pd.DataFrame): Processed fuel data
            
        Returns:
            dict: Feature statistics
        """
        if not self.feature_columns:
            return {}
        
        stats = {}
        for col in self.feature_columns:
            if col in df.columns:
                stats[col] = {
                    'mean': df[col].mean(),
                    'std': df[col].std(),
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'correlation_with_efficiency': df[col].corr(df.get('fuel_efficiency', pd.Series()))
                }
        
        return stats
