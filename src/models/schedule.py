from sqlalchemy import Column, Integer, DateTime, ForeignKey, Time, Boolean
from sqlalchemy.orm import relationship
from src.bot.database import Base

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    engineer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)  # work start time
    end_time = Column(Time, nullable=False)    # work end time
    break_start_time = Column(Time, nullable=True)  # optional break start
    break_end_time = Column(Time, nullable=True)    # optional break end
    is_active = Column(Boolean, default=True)

    # Relationships
    engineer = relationship("User", back_populates="schedule_entries")

    def __repr__(self):
        return f"<Schedule(id={self.id}, engineer_id={self.engineer_id}, day_of_week={self.day_of_week}, start_time={self.start_time}, end_time={self.end_time})>"