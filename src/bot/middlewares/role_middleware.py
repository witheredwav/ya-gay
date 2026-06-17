from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from src.bot.database import async_session
from src.bot.config import config
from sqlalchemy import select
from src.models.user import User

class RoleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Extract user from event
        telegram_user: User = data.get("event_from_user")
        if not telegram_user:
            return await handler(event, data)

        # Get or create user in DB
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_user.id)
            )
            user = result.scalar_one_or_none()
            if not user:
                # Create new user (client by default)
                user = User(
                    telegram_id=telegram_user.id,
                    username=telegram_user.username,
                    first_name=telegram_user.first_name,
                    last_name=telegram_user.last_name,
                    role="client"
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
            # Add user to data for handlers
            data["user"] = user
            # Add is_admin flag
            data["is_admin"] = user.role == "admin" or user.telegram_id in config.ADMIN_IDS
            data["is_engineer"] = user.role == "engineer"
            data["is_client"] = user.role == "client"

        return await handler(event, data)