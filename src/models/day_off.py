from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from src.bot.database import Base

class DayOff(Base):
    __tablename__ = "days_off"

    id = Column(Integer, primary_key=True, index=True)
    engineer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)  # specific date
    reason = Column(String(255), nullable=True)

    # Relationships
    engineer = relationship("User", back_populates="days_off")

    def __repr__(self):
        return f"<DayOff(id={self.id}, engineer_id={self.engineer_id}, date={self.date})>"