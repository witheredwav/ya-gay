from sqlalchemy import Column, Integer, String, Time
from src.bot.database import Base

class StudioSettings(Base):
    __tablename__ = "studio_settings"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    work_hours_start = Column(Time, nullable=True)
    work_hours_end = Column(Time, nullable=True)

    def __repr__(self):
        return f"<StudioSettings(id={self.id}, phone='{self.phone}', email='{self.email}', address='{self.address}')>"