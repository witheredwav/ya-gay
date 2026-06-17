from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.bot.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    registration_date = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    role = Column(String(20), nullable=False)  # 'client', 'engineer', 'admin'
    # For engineers
    hourly_rate = Column(Integer, nullable=True)  # in currency units
    description = Column(Text, nullable=True)
    photo_file_id = Column(String(255), nullable=True)  # Telegram photo file_id
    contact_info_sharing_allowed = Column(Boolean, default=False)
    # For admins, no extra fields needed

    # Relationships
    # bookings as client
    bookings_as_client = relationship("Booking", foreign_keys="Booking.client_id", back_populates="client")
    # bookings as engineer
    bookings_as_engineer = relationship("Booking", foreign_keys="Booking.engineer_id", back_populates="engineer")
    # bonus transactions
    bonus_transactions = relationship("BonusTransaction", back_populates="user")
    # referrals where this user is the referrer
    referrals_made = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")
    # referrals where this user is the referred
    referrals_received = relationship("Referral", foreign_keys="Referral.referred_id", back_populates="referred")
    # schedule
    schedule_entries = relationship("Schedule", back_populates="engineer")
    # days off
    days_off = relationship("DayOff", back_populates="engineer")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, role={self.role})>"