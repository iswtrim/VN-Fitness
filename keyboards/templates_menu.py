from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def templates_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Добавить шаблон', callback_data='add_template')],
        [InlineKeyboardButton(text='Удалить шаблон', callback_data='delete_template')],
        [InlineKeyboardButton(text='Посмотреть мои шаблоны', callback_data='view_templates')],
        [InlineKeyboardButton(text='Вернуться в главное меню', callback_data='back_to_main')]
    ])