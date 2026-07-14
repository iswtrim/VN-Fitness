from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_parameters_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Добавить параметры', callback_data='add_parameters')],
        [InlineKeyboardButton(text='Посмотреть мои записи', callback_data='view_parameters')],
        [InlineKeyboardButton(text='Вернуться в главное меню', callback_data='back_to_main')]
    ])
