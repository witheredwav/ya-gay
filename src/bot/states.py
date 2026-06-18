from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()

class BookingStates(StatesGroup):
    choosing_month = State()
    choosing_date = State()
    choosing_engineer = State()
    choosing_time = State()
    entering_name = State()
    entering_phone = State()
    choosing_duration = State()
    confirming = State()

class NightBookingStates(StatesGroup):
    choosing_engineer = State()
    choosing_date = State()
    choosing_time = State()
    choosing_duration = State()
    confirming = State()

class ProfileStates(StatesGroup):
    choosing_field = State()
    entering_value = State()

class AdminStates(StatesGroup):
    adding_engineer = State()
    adding_admin = State()
    viewing_clients = State()
    viewing_client_details = State()
    # Studio settings editing
    editing_studio_phone = State()
    editing_studio_email = State()
    editing_studio_address = State()
    # Engineer details editing
    editing_engineer_hourly_rate = State()
    editing_engineer_description = State()
    editing_engineer_photo = State()

class BonusStates(StatesGroup):
    viewing_balance = State()
    choosing_reward = State()
    confirming_spend = State()