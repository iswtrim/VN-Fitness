from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from config import ALLOWED_USER_IDS


class AccessMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id

        if user_id not in ALLOWED_USER_IDS:
            # Блокируем: не вызываем handler, отправляем сообщение
            await event.answer("⛔ Доступ запрещён.")
            return  # выходим

        # Пропускаем
        return await handler(event, data)
