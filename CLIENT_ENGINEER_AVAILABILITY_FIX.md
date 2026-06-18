# Fix for Engineer Availability Check and Dynamic Engineer Keyboard

## Problem
1. Engineer keyboard is hardcoded to show only 2 engineers (IDs 1 and 2) instead of fetching from database
2. When an engineer has no available slots, the bot only tells the user to choose a different date or engineer, but doesn't check if ALL engineers are unavailable
3. User requests a button/message when all engineers are unavailable (day off or fully booked)

## Solution
Modify `src/bot/handlers/client.py` to:
1. Create a dynamic engineer keyboard that fetches engineers from the database
2. Enhance the engineer selection handler to check if ALL engineers are unavailable
3. Show appropriate message when no engineers are available

## Changes to Make

### 1. Replace the `get_engineer_keyboard` function

Replace lines 38-45 in `src/bot/keyboards/client.py`:

**CURRENT CODE:**
```python
def get_engineer_keyboard():
    builder = InlineKeyboardBuilder()
    # In reality, fetch from DB
    builder.button(text="Инженер 1", callback_data="engineer:1")
    builder.button(text="Инженер 2", callback_data="engineer:2")
    builder.button(text="🔙 Назад", callback_data="back_to_date")
    builder.adjust(2)
    return builder.as_markup()
```

**NEW CODE:**
```python
def get_engineer_keyboard(engineers):
    builder = InlineKeyboardBuilder()
    for engineer in engineers:
        # Show engineer's name or fallback to ID
        name = f"{engineer.first_name} {engineer.last_name or ''}".strip()
        if not name:
            name = f"Инженер {engineer.id}"
        builder.button(text=name, callback_data=f"engineer:{engineer.id}")
    builder.button(text="🔙 Назад", callback_data="back_to_date")
    builder.adjust(2)
    return builder.as_markup()
```

### 2. Import the get_engineers function in client.py

Add this import at the top of `src/bot/handlers/client.py` with other imports:
```python
from src.bot.handlers.client import get_engineers
```

### 3. Modify the month and date selection handlers to pass engineers to the keyboard

In the `process_month` function (around line 247), after getting the date keyboard, we'll need to modify how we handle engineer selection later.

Actually, we need to modify the engineer selection handler to fetch engineers and check availability.

### 4. Replace the engineer selection handler (process_engineer)

Replace lines 274-303 in `src/bot/handlers/client.py`:

**CURRENT CODE:**
```python
# Engineer selection handler
@router.callback_query(F.data.startswith("engineer:"), BookingStates.choosing_engineer)
async def process_engineer(callback: CallbackQuery, state: FSMContext):
    engineer_id = int(callback.data.split(":")[1])
    await state.update_data(engineer_id=engineer_id)
    await state.set_state(BookingStates.choosing_time)
    data = await state.get_data()
    year = data["year"]
    month = data["month"]
    day = data["day"]
    date = datetime(year, month, day).date()
    free_slots = await get_free_slots(engineer_id, date)
    if not free_slots:
        await callback.message.edit_text(
            "На выбранную дату у этого инженера нет свободных слотов. Выберите другую дату или инженера.",
            reply_markup=get_date_keyboard(month)
        )
        await state.set_state(BookingStates.choosing_date)
        await callback.answer()
        return
    # Build keyboard with free slots
    builder = InlineKeyboardBuilder()
    for slot in free_slots:
        builder.button(text=slot.strftime("%H:%M"), callback_data=f"time:{slot.strftime('%H:%M')}")
    builder.button(text="🔙 Назад", callback_data="back_to_date")
    builder.adjust(4, 1)
    await callback.message.edit_text(
        "Выберите время:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()
```

**NEW CODE:**
```python
# Engineer selection handler
@router.callback_query(F.data.startswith("engineer:"), BookingStates.choosing_engineer)
async def process_engineer(callback: CallbackQuery, state: FSMContext):
    engineer_id = int(callback.data.split(":")[1])
    await state.update_data(engineer_id=engineer_id)
    data = await state.get_data()
    year = data["year"]
    month = data["month"]
    day = data["day"]
    date = datetime(year, month, day).date()
    
    # Get all active engineers
    async with async_session() as session:
        engineers = await get_engineers(session)
        
        # Check if we have any engineers at all
        if not engineers:
            await callback.message.edit_text(
                "В системе нет доступных инженеров. Обратитесь к администратору.",
                reply_markup=get_main_client_keyboard()
            )
            await state.clear()
            await callback.answer()
            return
        
        # Check availability for ALL engineers
        all_unavailable = True
        available_engineers = []
        
        for engineer in engineers:
            free_slots = await get_free_slots(engineer.id, date)
            if free_slots:
                all_unavailable = False
                available_engineers.append(engineer)
        
        # If ALL engineers are unavailable, show special message
        if all_unavailable:
            await callback.message.edit_text(
                "Сегодня все инженеры недоступны (выходной или все слоты заняты). "
                "Пожалуйста, выберите другую дату.",
                reply_markup=get_date_keyboard(month)
            )
            await state.set_state(BookingStates.choosing_date)
            await callback.answer()
            return
        
        # If the selected engineer is unavailable but others are available
        selected_engineer = next((e for e in engineers if e.id == engineer_id), None)
        if selected_engineer:
            free_slots = await get_free_slots(selected_engineer.id, date)
            if not free_slots:
                # Build keyboard with AVAILABLE engineers only
                builder = InlineKeyboardBuilder()
                for engineer in available_engineers:
                    name = f"{engineer.first_name} {engineer.last_name or ''}".strip()
                    if not name:
                        name = f"Инженер {engineer.id}"
                    builder.button(text=name, callback_data=f"engineer:{engineer.id}")
                builder.button(text="🔙 Назад к датам", callback_data="back_to_date")
                builder.adjust(2)
                
                await callback.message.edit_text(
                    f"У инженера {selected_engineer.first_name} {selected_engineer.last_name or ''} "
                    f"на выбранную дату нет свободных слотов. "
                    f"Пожалуйста, выберите другого инженера:",
                    reply_markup=builder.as_markup()
                )
                await callback.answer()
                return
        
        # If we get here, the selected engineer has availability
        await state.update_data(engineer_id=engineer_id)
        await state.set_state(BookingStates.choosing_time)
        
        # Build keyboard with free slots for the selected engineer
        builder = InlineKeyboardBuilder()
        for slot in free_slots:
            builder.button(text=slot.strftime("%H:%M"), callback_data=f"time:{slot.strftime('%H:%M')}")
        builder.button(text="🔙 Назад", callback_data="back_to_engineer")
        builder.adjust(4, 1)
        await callback.message.edit_text(
            "Выберите время:",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
```

## How It Works

1. **Dynamic Engineer Keyboard**: The `get_engineer_keyboard` function now accepts a list of engineers and creates buttons for each one based on their actual data from the database.

2. **Availability Checking**: When an engineer is selected, the system:
   - Gets all active engineers from the database
   - Checks each engineer's availability for the selected date
   - If ALL engineers are unavailable (day off or fully booked), shows a message: "Сегодня все инженеры недоступны (выходной или все слоты заняты). Пожалуйста, выберите другую дату."
   - If ONLY the selected engineer is unavailable but others are available, shows a list of ONLY the available engineers for the user to choose from
   - If the selected engineer is available, proceeds with the normal time slot selection

## Additional Notes

1. **Performance**: This solution makes multiple database calls (one per engineer to check availability). For a small number of engineers (<10), this is acceptable. For larger numbers, consider optimizing by fetching all schedules and dayoffs in a single query.

2. **Admin Inclusion**: The `get_engineers` function includes both engineers and admins (users with role "engineer" OR "admin"). If you want to exclude admins from the engineer selection, modify the function to only include `User.role == "engineer"`.

3. **Fallback Names**: If an engineer doesn't have first/last name set, it falls back to showing "Инженер {id}".

## Files to Modify
1. `src/bot/keyboards/client.py` - Replace `get_engineer_keyboard` function
2. `src/bot/handlers/client.py` - Add import and replace `process_engineer` function

## Testing
After implementing these changes:
1. Apply the database migration fix (see DATABASE_FIX_INSTRUCTIONS.md)
2. Start the bot: `py -m src.bot.main`
3. Test the booking flow:
   - Select a date
   - Verify engineer list shows actual engineers from database
   - Select an engineer with no availability - should show list of available engineers
   - Select a date when all engineers are unavailable - should show "Сегодня все инженеры недоступно" message