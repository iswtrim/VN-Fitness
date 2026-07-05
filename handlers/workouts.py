from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from keyboards.workouts_menu import workouts_menu
from database.requests import get_or_create_user

router = Router()


@router.callback_query(F.data == 'workouts')
async def workouts(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Что ты хочешь сделать?', reply_markup=workouts_menu())
