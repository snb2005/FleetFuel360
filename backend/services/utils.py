"""
Utility Functions
Helper functions for data processing and common operations
"""

import pandas as pd
import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

def load_csv(filepath: str) -> pd.DataFrame:
    """
    Load CSV file into pandas DataFrame
    
    Args:
        filepath (str): Path to CSV file
        
    Returns:
        pd.DataFrame: Loaded data
    """
    try:
        df = pd.read_csv(filepath)
        print(f"✅ Loaded {len(df)} records from {filepath}")
        return df
    except Exception as e:
        print(f"❌ Error loading CSV {filepath}: {e}")
        raise

def save_csv(df: pd.DataFrame, filepath: str) -> bool:
    """
    Save DataFrame to CSV file
    
    Args:
        df (pd.DataFrame): Data to save
        filepath (str): Output file path
        
    Returns:
        bool: Success status
    """
    try:
        df.to_csv(filepath, index=False)
        print(f"✅ Saved {len(df)} records to {filepath}")
        return True
    except Exception as e:
        print(f"❌ Error saving CSV {filepath}: {e}")
        return False

def convert_units(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert between different units
    
    Args:
        value (float): Value to convert
        from_unit (str): Source unit
        to_unit (str): Target unit
        
    Returns:
        float: Converted value
    """
    # Distance conversions
    distance_conversions = {
        ('km', 'miles'): 0.621371,
        ('miles', 'km'): 1.60934,
        ('km', 'm'): 1000,
        ('m', 'km'): 0.001
    }
    
    # Volume conversions (liters base)
    volume_conversions = {
        ('l', 'gal'): 0.264172,  # liters to gallons (US)
        ('gal', 'l'): 3.78541,   # gallons (US) to liters
        ('l', 'ml'): 1000,
        ('ml', 'l'): 0.001
    }
    
    conversion_key = (from_unit.lower(), to_unit.lower())
    
    if conversion_key in distance_conversions:
        return value * distance_conversions[conversion_key]
    elif conversion_key in volume_conversions:
        return value * volume_conversions[conversion_key]
    elif from_unit.lower() == to_unit.lower():
        return value
    else:
        raise ValueError(f"Conversion from {from_unit} to {to_unit} not supported")

def calculate_fuel_efficiency(km_driven: float, fuel_used: float, unit: str = 'km/l') -> float:
    """
    Calculate fuel efficiency in specified units
    
    Args:
        km_driven (float): Distance driven
        fuel_used (float): Fuel consumed
        unit (str): Output unit ('km/l', 'mpg', 'l/100km')
        
    Returns:
        float: Fuel efficiency
    """
    if fuel_used <= 0:
        return 0
    
    if unit.lower() == 'km/l':
        return km_driven / fuel_used
    elif unit.lower() == 'mpg':
        miles = convert_units(km_driven, 'km', 'miles')
        gallons = convert_units(fuel_used, 'l', 'gal')
        return miles / gallons if gallons > 0 else 0
    elif unit.lower() == 'l/100km':
        return (fuel_used / km_driven) * 100 if km_driven > 0 else 0
    else:
        raise ValueError(f"Unit {unit} not supported")

def format_timestamp(timestamp: Any) -> str:
    """
    Format timestamp to ISO string
    
    Args:
        timestamp: Timestamp in various formats
        
    Returns:
        str: ISO formatted timestamp string
    """
    if isinstance(timestamp, str):
        try:
            dt = pd.to_datetime(timestamp)
            return dt.isoformat()
        except:
            return timestamp
    elif isinstance(timestamp, datetime):
        return timestamp.isoformat()
    elif hasattr(timestamp, 'isoformat'):
        return timestamp.isoformat()
    else:
        return str(timestamp)

def parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse timestamp string to datetime object
    
    Args:
        timestamp_str (str): Timestamp string
        
    Returns:
        datetime: Parsed datetime object
    """
    try:
        return pd.to_datetime(timestamp_str).to_pydatetime()
    except:
        raise ValueError(f"Cannot parse timestamp: {timestamp_str}")

def get_date_range(days_back: int = 30) -> tuple:
    """
    Get date range for the last N days
    
    Args:
        days_back (int): Number of days to go back
        
    Returns:
        tuple: (start_date, end_date)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    return start_date, end_date

def validate_fuel_data(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean a fuel log record
    
    Args:
        record (dict): Fuel log record
        
    Returns:
        dict: Validated record
    """
    validated = record.copy()
    
    # Required fields
    required_fields = ['vehicle_id', 'timestamp', 'km_driven', 'fuel_used']
    for field in required_fields:
        if field not in validated:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate numeric fields
    try:
        validated['km_driven'] = float(validated['km_driven'])
        validated['fuel_used'] = float(validated['fuel_used'])
        
        if validated['km_driven'] <= 0:
            raise ValueError("km_driven must be positive")
        if validated['fuel_used'] <= 0:
            raise ValueError("fuel_used must be positive")
            
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid numeric values: {e}")
    
    # Validate timestamp
    try:
        validated['timestamp'] = parse_timestamp(str(validated['timestamp']))
    except:
        raise ValueError(f"Invalid timestamp format: {validated['timestamp']}")
    
    # Calculate efficiency
    validated['fuel_efficiency'] = calculate_fuel_efficiency(
        validated['km_driven'], 
        validated['fuel_used']
    )
    
    return validated

def aggregate_by_vehicle(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate fuel data by vehicle
    
    Args:
        df (pd.DataFrame): Fuel log data
        
    Returns:
        pd.DataFrame: Aggregated data by vehicle
    """
    if 'fuel_efficiency' not in df.columns:
        df['fuel_efficiency'] = df['km_driven'] / df['fuel_used']
    
    agg_data = df.groupby('vehicle_id').agg({
        'km_driven': ['sum', 'mean', 'count'],
        'fuel_used': ['sum', 'mean'],
        'fuel_efficiency': ['mean', 'std', 'min', 'max'],
        'timestamp': ['min', 'max']
    }).round(2)
    
    # Flatten column names
    agg_data.columns = ['_'.join(col).strip() for col in agg_data.columns]
    agg_data = agg_data.reset_index()
    
    # Rename for clarity
    column_mapping = {
        'km_driven_sum': 'total_km',
        'km_driven_mean': 'avg_km_per_trip',
        'km_driven_count': 'total_trips',
        'fuel_used_sum': 'total_fuel',
        'fuel_used_mean': 'avg_fuel_per_trip',
        'fuel_efficiency_mean': 'avg_efficiency',
        'fuel_efficiency_std': 'efficiency_std',
        'fuel_efficiency_min': 'min_efficiency',
        'fuel_efficiency_max': 'max_efficiency',
        'timestamp_min': 'first_record',
        'timestamp_max': 'last_record'
    }
    
    agg_data = agg_data.rename(columns=column_mapping)
    
    return agg_data

def generate_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics for fuel data
    
    Args:
        df (pd.DataFrame): Fuel log data
        
    Returns:
        dict: Summary statistics
    """
    if df.empty:
        return {"status": "no_data"}
    
    # Calculate efficiency if not present
    if 'fuel_efficiency' not in df.columns:
        df = df.copy()
        df['fuel_efficiency'] = df['km_driven'] / df['fuel_used']
    
    stats = {
        'total_records': len(df),
        'unique_vehicles': df['vehicle_id'].nunique(),
        'date_range': {
            'start': str(df['timestamp'].min()) if 'timestamp' in df.columns else None,
            'end': str(df['timestamp'].max()) if 'timestamp' in df.columns else None
        },
        'totals': {
            'km_driven': float(df['km_driven'].sum()),
            'fuel_used': float(df['fuel_used'].sum()),
            'avg_efficiency': float(df['fuel_efficiency'].mean())
        },
        'efficiency_stats': {
            'mean': float(df['fuel_efficiency'].mean()),
            'median': float(df['fuel_efficiency'].median()),
            'std': float(df['fuel_efficiency'].std()),
            'min': float(df['fuel_efficiency'].min()),
            'max': float(df['fuel_efficiency'].max())
        },
        'vehicle_breakdown': df['vehicle_id'].value_counts().to_dict()
    }
    
    return stats

def detect_outliers_iqr(series: pd.Series, factor: float = 1.5) -> pd.Series:
    """
    Detect outliers using Interquartile Range (IQR) method
    
    Args:
        series (pd.Series): Data series
        factor (float): IQR multiplication factor
        
    Returns:
        pd.Series: Boolean series indicating outliers
    """
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - factor * IQR
    upper_bound = Q3 + factor * IQR
    
    return (series < lower_bound) | (series > upper_bound)

def format_number(value: float, precision: int = 2) -> str:
    """
    Format number with specified precision
    
    Args:
        value (float): Number to format
        precision (int): Decimal places
        
    Returns:
        str: Formatted number string
    """
    try:
        return f"{float(value):.{precision}f}"
    except:
        return str(value)

def create_time_series_data(df: pd.DataFrame, freq: str = 'D') -> pd.DataFrame:
    """
    Create time series data grouped by frequency
    
    Args:
        df (pd.DataFrame): Fuel log data with timestamp
        freq (str): Frequency ('D', 'H', 'W', 'M')
        
    Returns:
        pd.DataFrame: Time series data
    """
    if 'timestamp' not in df.columns:
        raise ValueError("DataFrame must contain 'timestamp' column")
    
    df_ts = df.copy()
    df_ts['timestamp'] = pd.to_datetime(df_ts['timestamp'])
    df_ts = df_ts.set_index('timestamp')
    
    # Group by frequency and aggregate
    ts_data = df_ts.groupby([df_ts.index.to_period(freq), 'vehicle_id']).agg({
        'km_driven': 'sum',
        'fuel_used': 'sum',
        'fuel_efficiency': 'mean'
    }).reset_index()
    
    ts_data['timestamp'] = ts_data['timestamp'].dt.to_timestamp()
    
    return ts_data.sort_values(['timestamp', 'vehicle_id'])

def export_anomalies_report(anomalies_df: pd.DataFrame, filepath: str) -> bool:
    """
    Export anomalies to a formatted report
    
    Args:
        anomalies_df (pd.DataFrame): Anomalies data
        filepath (str): Output file path
        
    Returns:
        bool: Success status
    """
    try:
        # Create a formatted report
        report_data = anomalies_df.copy()
        
        # Format numeric columns
        numeric_cols = ['km_driven', 'fuel_used', 'fuel_efficiency', 'anomaly_score']
        for col in numeric_cols:
            if col in report_data.columns:
                report_data[col] = report_data[col].apply(lambda x: format_number(x))
        
        # Format timestamp
        if 'timestamp' in report_data.columns:
            report_data['timestamp'] = report_data['timestamp'].apply(format_timestamp)
        
        # Save to CSV
        report_data.to_csv(filepath, index=False)
        print(f"✅ Anomalies report saved to: {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving anomalies report: {e}")
        return False
