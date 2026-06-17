from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.bot.database import Base
import enum

class ReferralStatus(str, enum.Enum):
    PENDING = "pending"  # user signed up via referral link
    CONFIRMED = "confirmed"  # referred user completed a booking that was recorded
    REJECTED = "rejected"  # referral did not meet conditions

class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referred_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ReferralStatus), default=ReferralStatus.PENDING)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)  # the booking that confirmed the referral
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referrals_received")
    booking = relationship("Booking", back_populates="referral")

    def __repr__(self):
        return f"<Referral(id={self.id}, referrer_id={self.referrer_id}, referred_id={self.referred_id}, status='{self.status}')>"