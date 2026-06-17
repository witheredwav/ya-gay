from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.bot.database import Base

class BonusTransaction(Base):
    __tablename__ = "bonus_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # positive for earning, negative for spending
    reason = Column(String(100), nullable=False)  # e.g., 'visit', 'referral', 'reward_1', 'reward_2'
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="bonus_transactions")
    booking = relationship("Booking", back_populates="bonus_transactions")

    def __repr__(self):
        return f"<BonusTransaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, reason='{self.reason}')>"