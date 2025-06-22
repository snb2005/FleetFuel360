"""
Vehicle Model
SQLAlchemy model for vehicles table
"""

from sqlalchemy import Column, Integer, String, DateTime, func, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Vehicle(Base):
    """
    Vehicle model representing trucks in the fleet
    """
    __tablename__ = 'vehicles'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Vehicle identification
    vehicle_id = Column(String(20), unique=True, nullable=False, index=True)
    make = Column(String(50))
    model = Column(String(50))
    year = Column(Integer)
    fuel_capacity = Column(Numeric(5, 2))
    
    # Timestamps
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    fuel_logs = relationship("FuelLog", back_populates="vehicle", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Vehicle(vehicle_id='{self.vehicle_id}', make='{self.make}', model='{self.model}')>"
    
    def to_dict(self):
        """Convert vehicle object to dictionary"""
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'make': self.make,
            'model': self.model,
            'year': self.year,
            'fuel_capacity': float(self.fuel_capacity) if self.fuel_capacity else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_vehicle_id(cls, session, vehicle_id):
        """Get vehicle by vehicle_id"""
        return session.query(cls).filter(cls.vehicle_id == vehicle_id).first()
    
    @classmethod
    def get_all(cls, session):
        """Get all vehicles"""
        return session.query(cls).order_by(cls.vehicle_id).all()
    
    @property
    def total_fuel_logs(self):
        """Get total number of fuel logs for this vehicle"""
        return len(self.fuel_logs)
    
    @property
    def average_efficiency(self):
        """Calculate average fuel efficiency for this vehicle"""
        if not self.fuel_logs:
            return 0
        
        total_efficiency = sum(log.fuel_efficiency for log in self.fuel_logs if log.fuel_efficiency)
        return total_efficiency / len(self.fuel_logs) if self.fuel_logs else 0
