"""User Department association model."""

from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from ..db.base import Base


class UserDepartment(Base):
    """User Department association model."""
    
    __tablename__ = "user_departments"
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True, primary_key=True)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False, index=True, primary_key=True)
    is_primary = Column(Boolean, default=True, nullable=False)  # 是否为主要部门
    is_active = Column(Boolean, default=True, nullable=False)   # 是否激活
    
    # 关系
    user = relationship("User", back_populates="user_departments")
    department = relationship("Department", back_populates="user_departments")
    
    def __repr__(self):
        return f"<UserDepartment(user_id={self.user_id}, department_id={self.department_id}, is_primary={self.is_primary})>"
    
    def to_dict(self):
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'department_id': self.department_id,
            'is_primary': self.is_primary,
            'is_active': self.is_active
        })
        return data