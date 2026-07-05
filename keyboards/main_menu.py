from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Тренировки', callback_data='workouts')],
        [InlineKeyboardButton(text='Шаблоны', callback_data='templates')],
        [InlineKeyboardButton(text='Параметры', callback_data='parameters')]
    ])
