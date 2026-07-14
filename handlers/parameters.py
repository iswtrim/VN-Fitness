from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from datetime import datetime

from keyboards.parameters_menu import get_parameters_menu
from database.requests import get_or_create_user, save_parameters, get_parameters, get_parameter_details, \
    delete_parameter_by_id

router = Router()


class AddParameters(StatesGroup):
    waiting_for_weight = State()  # ждём вес в кг
    waiting_for_parameters = State()  # ждём свободный текст


@router.callback_query(F.data == 'parameters')
async def parameters_menu(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Что хочешь сделать?', reply_markup=get_parameters_menu())


@router.callback_query(F.data == 'add_parameters')
async def start_add_parameters(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    await state.set_state(AddParameters.waiting_for_weight)
    await callback.message.edit_text(
        'Напиши свой вес в килограммах (только число):\n\n'
        'Пример: 45 или 54.6'
    )


@router.message(AddParameters.waiting_for_weight)
async def get_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text.replace(',', '.'))
    except ValueError:
        await message.answer('❌ Напиши число. Например: 51 или 63.8')
        return

    await state.update_data(weight=weight)
    await state.set_state(AddParameters.waiting_for_parameters)

    await message.answer(
        'Теперь напиши остальные параметры тела в свободной форме.\n\n'
        'Пример: об=90, от=60, подтягиваюсь 8 раз\n\n'
        'Или просто напиши -, если не хочешь заполнять.'
    )


@router.message(AddParameters.waiting_for_parameters)
async def get_parameters_text(message: Message, state: FSMContext):
    data = await state.get_data()
    weight = data.get('weight')
    parameters_text = message.text.strip()

    user_id = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username
    )

    await save_parameters(user_id, weight, parameters_text)

    text = f"✅ Параметры сохранены!\n\n"
    text += f"📊 Вес: {weight} кг\n"
    text += f"📋 Параметры: {parameters_text}\n"
    text += f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📏 К параметрам', callback_data='parameters')],
        [InlineKeyboardButton(text='🏠 В главное меню', callback_data='back_to_main')]
    ])

    await message.answer(text, reply_markup=keyboard)
    await state.clear()


@router.callback_query(F.data == 'view_parameters')
async def view_parameters(callback: CallbackQuery):
    await callback.answer('')

    user_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username
    )

    records, total = await get_parameters(user_id, offset=0)

    if not records:
        await callback.message.edit_text(
            'У тебя пока нет записей параметров :(\n\n'
            'Добавь первую через кнопку "Добавить параметры".',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='↩️ Назад', callback_data='parameters')]
            ])
        )
        return

    # Клавиатура с записями
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for r in records:
        date_str = r['date'].strftime('%d.%m.%Y')
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"📅 {date_str} — {r['weight']} кг",
                callback_data=f'view_parameter_{r["id"]}'
            )
        ])

    # Кнопки навигации
    nav_buttons = [(InlineKeyboardButton(text='↩️ В меню', callback_data='parameters'))]

    if total > 3:
        nav_buttons.append(InlineKeyboardButton(text='➡️ Вперёд', callback_data='parameters_page_1'))

    keyboard.inline_keyboard.append(nav_buttons)

    await callback.message.edit_text(
        f'📏 Твои записи (всего: {total}):',
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('parameters_page_'))
async def paginate_parameters(callback: CallbackQuery):
    await callback.answer('')

    page = int(callback.data.split('_')[-1])
    offset = page * 3

    user_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username
    )

    records, total = await get_parameters(user_id, offset=offset)

    if not records:
        await callback.answer('Больше записей нет.', show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for r in records:
        date_str = r['date'].strftime('%d.%m.%Y')
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"📅 {date_str} — {r['weight']} кг",
                callback_data=f'view_parameter_{r["id"]}'
            )
        ])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text='⬅️ Назад', callback_data=f'parameters_page_{page - 1}'))
    if (page + 1) * 3 < total:
        nav_buttons.append(InlineKeyboardButton(text='➡️ Вперёд', callback_data=f'parameters_page_{page + 1}'))
    nav_buttons.append(InlineKeyboardButton(text='↩️ В меню', callback_data='parameters'))
    keyboard.inline_keyboard.append(nav_buttons)

    await callback.message.edit_text(
        f'📏 Твои записи (страница {page + 1}, всего: {total}):',
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('view_parameter_'))
async def view_parameter_detail(callback: CallbackQuery):
    await callback.answer('')

    parameter_id = int(callback.data.split('_')[-1])
    record = await get_parameter_details(parameter_id)

    if not record:
        await callback.message.edit_text(
            'Запись не найдена.',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='↩️ Назад', callback_data='view_parameters')]
            ])
        )
        return

    date_str = record['date'].strftime('%d.%m.%Y %H:%M')

    text = f"📏 Запись от {date_str}\n\n"
    text += f"📊 Вес: {record['weight']} кг\n"
    text += f"📋 Параметры: {record['parameters'] or 'не указано'}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🗑️ Удалить запись', callback_data=f'confirm_delete_parameter_{record["id"]}|{date_str}')],
        [InlineKeyboardButton(text='📋 Назад к списку параметров', callback_data='view_parameters')],
        [InlineKeyboardButton(text='↩️ В меню параметров', callback_data='parameters')]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith('confirm_delete_parameter_'))
async def confirm_delete_parameter(callback: CallbackQuery):
    await callback.answer('')

    parts = callback.data.split('|')
    parameter_id = int(parts[0].split('_')[-1])
    date_str = parts[1] if len(parts) > 1 else "Неизвестная дата"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✅ Да, удалить', callback_data=f'delete_parameter_{parameter_id}'),
            InlineKeyboardButton(text='❌ Нет, оставить', callback_data=f'view_parameter_{parameter_id}')
        ],
        [InlineKeyboardButton(text='↩️ В меню параметров', callback_data='parameters')]
    ])
    await callback.message.edit_text(
        f"⚠️ Ты уверен, что хочешь удалить запись от {date_str}?\n\nЭто действие нельзя отменить.",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('delete_parameter_'))
async def delete_parameter(callback: CallbackQuery):
    await callback.answer('')

    parameter_id = int(callback.data.split('_')[-1])
    await delete_parameter_by_id(parameter_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📋 Назад к списку параметров', callback_data='view_parameters')],
        [InlineKeyboardButton(text='↩️ В меню параметров', callback_data='parameters')]
    ])
    await callback.message.edit_text(
        "✅ Запись успешно удалена!",
        reply_markup=keyboard
    )
