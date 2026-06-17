from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.bot.database import Base
import enum

class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED_CLIENT = "cancelled_client"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    # For internal use: recording happened
    RECORDED = "recorded"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    engineer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    duration_hours = Column(Integer, nullable=False)  # 1,2,3,4,5,6
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    is_night_booking = Column(Boolean, default=False)
    total_price = Column(Integer, nullable=True)  # calculated from duration_hours * engineer.hourly_rate
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    client = relationship("User", foreign_keys=[client_id], back_populates="bookings_as_client")
    engineer = relationship("User", foreign_keys=[engineer_id], back_populates="bookings_as_engineer")
    # bonus transactions related to this booking
    bonus_transactions = relationship("BonusTransaction", back_populates="booking")
    # referral related to this booking (if this booking caused a referral bonus)
    referral = relationship("Referral", uselist=False, back_populates="booking")

    def __repr__(self):
        return f"<Booking(id={self.id}, client_id={self.client_id}, engineer_id={self.engineer_id}, start_time={self.start_time})>"