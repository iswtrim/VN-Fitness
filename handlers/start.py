from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from keyboards.main_menu import get_main_keyboard
from database.requests import get_or_create_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username
    )

    await message.answer(
        'Привет! Я твой личный бот для записи тренировок и параметров тела. С чего начнём?\n\nИспользуй команду /help, если не знаешь.',
        reply_markup=get_main_keyboard())


@router.message(Command('help'))
async def get_help(message: Message, state: FSMContext):
    await state.clear()

    text_message = '''
<b>🤖 Помощь по боту</b>

<i>Разделы:</i>
═══════════════════
📋 <b>Шаблоны:</b> добавить, посмотреть, удалить
🏋️‍♀️ <b>Тренировки:</b> добавить по шаблону, история
📏 <b>Параметры:</b> записать, посмотреть

<i>Команды:</i>
═══════════════════
🏠 /get_main_menu — если нужно вернуться в главное меню
💪 /get_motivation — если необходимо получить порцию мотивации
'''
    await message.answer(text_message, parse_mode='HTML')


@router.message(Command('get_motivation'))
async def get_motivation(message: Message, state: FSMContext):
    await state.clear()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🏠 Вернуться в главное меню', callback_data='back_to_main')]
    ])

    await message.answer_photo(
        photo='AgACAgIAAxkBAAMyahh244kTaz-17KK39kH9nM_y7_kAAkUdaxvhlcBIREmx3ZS7dGUBAAMCAANtAAM7BA',
        caption='Мотивацию надо поднять!!!',
        reply_markup=keyboard
    )


@router.message(Command('get_main_menu'))
async def get_main_menu(message: Message, state: FSMContext):
    await state.clear()

    await message.answer('Что тебя интересует?', reply_markup=get_main_keyboard())


@router.callback_query(F.data == 'back_to_main')
async def back_to_main_menu(callback: CallbackQuery):
    await callback.answer('')

    # Проверяем, есть ли текст в сообщении
    if callback.message.text:
        await callback.message.edit_text(
            'Что тебя интересует?',
            reply_markup=get_main_keyboard()
        )
    else:
        await callback.message.answer(
            'Что тебя интересует?',
            reply_markup=get_main_keyboard()
        )
