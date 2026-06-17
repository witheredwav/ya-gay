import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    ADMIN_IDS: List[int] = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

    # Additional settings
    WORKDAY_START: str = "11:00"
    WORKDAY_END: str = "22:00"
    TIME_SLOT_MINUTES: int = 30
    NIGHT_BOOKING_START: str = "22:00"
    NIGHT_BOOKING_END: str = "08:00"  # next day

    # Bonus settings
    REFERRAL_BONUS: int = 2
    VISIT_BONUS: int = 2
    BONUS_REWARD_1_COST: int = 10
    BONUS_REWARD_2_COST: int = 20

config = Config()