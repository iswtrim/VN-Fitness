from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# trainings = ['Тренировка 1.05', 'Тренировка 3.05', 'Тренировка 5.05']
#
# async def inline_trainings():
#     keyboard = InlineKeyboardBuilder()
#
#     for train in trainings:
#         keyboard.add(InlineKeyboardButton(text=train, url='https://youtube.com'))
#
#     return keyboard.adjust(3).as_markup()


def workouts_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Добавить тренировку по шаблону', callback_data='add_workout')],
        [InlineKeyboardButton(text='Посмотреть историю тренировок', callback_data='history_of_workouts')],
        [InlineKeyboardButton(text='Вернуться в главное меню', callback_data='back_to_main')]
    ])
