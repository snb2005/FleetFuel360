"""
Fuel Log Model
SQLAlchemy model for fuel_logs table
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func, text, Numeric, Computed
from sqlalchemy.orm import relationship
from .vehicle import Base

class FuelLog(Base):
    """
    Fuel log model representing individual fuel usage records
    """
    __tablename__ = 'fuel_logs'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to vehicles table
    vehicle_id = Column(String(20), ForeignKey('vehicles.vehicle_id'), nullable=False, index=True)
    
    # Fuel log data
    timestamp = Column(DateTime, nullable=False, index=True)
    km_driven = Column(Numeric(8, 2), nullable=False)
    fuel_used = Column(Numeric(6, 2), nullable=False)
    
    # Computed efficiency (generated column in database - auto-calculated)
    fuel_efficiency = Column(Numeric(6, 2), Computed("CASE WHEN fuel_used > 0 THEN km_driven / fuel_used ELSE 0 END", persisted=True))
    
    # Anomaly detection fields
    is_anomaly = Column(Boolean, default=False, index=True)
    anomaly_score = Column(Numeric(6, 4), default=0)
    
    # Timestamp
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="fuel_logs")
    
    def __repr__(self):
        return f"<FuelLog(vehicle_id='{self.vehicle_id}', timestamp='{self.timestamp}', efficiency={self.fuel_efficiency})>"
    
    def to_dict(self):
        """Convert fuel log object to dictionary"""
        # Handle timestamp conversion safely
        timestamp_str = None
        if self.timestamp:
            if hasattr(self.timestamp, 'isoformat'):
                timestamp_str = self.timestamp.isoformat()
            else:
                timestamp_str = str(self.timestamp)
        
        # Handle created_at conversion safely
        created_at_str = None
        if self.created_at:
            if hasattr(self.created_at, 'isoformat'):
                created_at_str = self.created_at.isoformat()
            else:
                created_at_str = str(self.created_at)
        
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'timestamp': timestamp_str,
            'km_driven': float(self.km_driven) if self.km_driven else None,
            'fuel_used': float(self.fuel_used) if self.fuel_used else None,
            'fuel_efficiency': float(self.fuel_efficiency) if self.fuel_efficiency else None,
            'is_anomaly': self.is_anomaly,
            'anomaly_score': float(self.anomaly_score) if self.anomaly_score else None,
            'created_at': created_at_str
        }
    
    @classmethod
    def get_by_vehicle(cls, session, vehicle_id, limit=None):
        """Get fuel logs for a specific vehicle"""
        query = session.query(cls).filter(cls.vehicle_id == vehicle_id).order_by(cls.timestamp.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @classmethod
    def get_all(cls, session, limit=None):
        """Get all fuel logs"""
        query = session.query(cls).order_by(cls.timestamp.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @classmethod
    def get_anomalies(cls, session, vehicle_id=None):
        """Get fuel logs that are marked as anomalies"""
        query = session.query(cls).filter(cls.is_anomaly == True)
        if vehicle_id:
            query = query.filter(cls.vehicle_id == vehicle_id)
        return query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_date_range(cls, session, start_date, end_date, vehicle_id=None):
        """Get fuel logs within a date range"""
        query = session.query(cls).filter(
            cls.timestamp >= start_date,
            cls.timestamp <= end_date
        )
        if vehicle_id:
            query = query.filter(cls.vehicle_id == vehicle_id)
        return query.order_by(cls.timestamp).all()
    
    @classmethod
    def get_efficiency_stats(cls, session, vehicle_id=None):
        """Get fuel efficiency statistics"""
        query = session.query(
            func.avg(cls.fuel_efficiency).label('avg_efficiency'),
            func.min(cls.fuel_efficiency).label('min_efficiency'),
            func.max(cls.fuel_efficiency).label('max_efficiency'),
            func.stddev(cls.fuel_efficiency).label('std_efficiency'),
            func.count(cls.id).label('total_records')
        )
        
        if vehicle_id:
            query = query.filter(cls.vehicle_id == vehicle_id)
        
        return query.first()
    
    def calculate_efficiency(self):
        """Calculate fuel efficiency (km per liter)"""
        if self.fuel_used and self.fuel_used > 0:
            return float(self.km_driven) / float(self.fuel_used)
        return 0
    
    def is_efficiency_anomaly(self, threshold_multiplier=2.0):
        """
        Check if this record is an efficiency anomaly
        Based on deviation from vehicle's average efficiency
        """
        if not self.vehicle or not self.fuel_efficiency:
            return False
        
        vehicle_avg = self.vehicle.average_efficiency
        if vehicle_avg == 0:
            return False
        
        deviation = abs(float(self.fuel_efficiency) - vehicle_avg) / vehicle_avg
        return deviation > threshold_multiplier
