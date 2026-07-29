from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def workouts_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Добавить тренировку по шаблону', callback_data='add_workout')],
        [InlineKeyboardButton(text='Посмотреть историю тренировок', callback_data='history_of_workouts')],
        [InlineKeyboardButton(text='Вернуться в главное меню', callback_data='back_to_main')]
    ])
