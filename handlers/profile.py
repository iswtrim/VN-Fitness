from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

router = Router()


@router.message(F.text.lower().in_(('айди', 'id')))
async def get_id(message: Message):
    client_id = message.from_user.id
    client_name = message.from_user.first_name
    await message.reply(f'{client_name}, твой айди - {client_id}')
