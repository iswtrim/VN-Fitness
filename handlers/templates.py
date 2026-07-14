from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from keyboards.templates_menu import templates_menu
from database.requests import get_or_create_user, save_template, get_templates, get_template_exercises, \
    delete_template_by_id

router = Router()


class AddTemplate(StatesGroup):
    waiting_for_template_name = State()  # ждём название шаблона
    waiting_for_exercises_count = State()  # ждём сколько упражнений
    waiting_for_exercise_name = State()  # ждём название упражнения
    waiting_for_sets_and_reps = State()  # ждём начальное количество подходов и повторений
    waiting_for_weight_or_rubber = State()  # ждём вес/резинку


@router.callback_query(F.data == 'templates')
async def workouts(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Что ты хочешь сделать?', reply_markup=templates_menu())


@router.callback_query(F.data == 'add_template')
async def add_workout_template(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    # Устанавливаем состояние waiting_for_template_name
    await state.set_state(AddTemplate.waiting_for_template_name)
    await callback.message.edit_text(
        'Отлично, приступим к созданию шаблона тренировки.\nДля начала скажи, как назовём этот шаблон?')


# Обработчик состояния waiting_for_template_name
@router.message(AddTemplate.waiting_for_template_name)
async def get_exercises_count(message: Message, state: FSMContext):
    # Сохраняем название шаблона во временные данные
    await state.update_data(template_name=message.text)

    # Переводим в состояние "жду количество упражнений"
    await state.set_state(AddTemplate.waiting_for_exercises_count)

    await message.answer(f'Супер, а сколько всего упражнений будет в шаблоне?\nНапиши только цифру.')


# Обработчик состояния waiting_for_exercises_count
@router.message(AddTemplate.waiting_for_exercises_count)
async def get_exercises_count(message: Message, state: FSMContext):
    try:
        count = int(message.text)
    except ValueError:
        await message.answer('Сколько упражнений будет в новом шаблоне?\nНапиши только цифру.')
        return

    # Сохраняем количество упражнений во временные данные
    await state.update_data(exercises_count=count)

    # Переводим в состояние "жду название упражнения"
    await state.set_state(AddTemplate.waiting_for_exercise_name)

    # Сохраняем счётчик, чтобы знать, сколько упражнений мы уже обработали
    current_exercise = 1
    await state.update_data(current_exercise=current_exercise)

    await message.answer(f'Напиши название {current_exercise}-го упражнения.')


@router.message(AddTemplate.waiting_for_exercise_name)
async def get_exercise_name(message: Message, state: FSMContext):
    # Получаем временные данные и текущий счётчик
    data = await state.get_data()
    current_exercise = data.get('current_exercise')

    # Сохраняем название n-ого упражнения во временные данные
    await state.update_data(**{f'exercise_{current_exercise}_name': message.text})

    # Переводим в состояние "жду количество подходов и повторений"
    await state.set_state(AddTemplate.waiting_for_sets_and_reps)

    await message.answer('Напиши количество подходов и повторений через "x", например 3 x 16.')


@router.message(AddTemplate.waiting_for_sets_and_reps)
async def get_exercise_sets_and_reps(message: Message, state: FSMContext):
    # Получаем временные данные и текущий счётчик
    data = await state.get_data()
    current_exercise = data.get('current_exercise')

    # Сохраняем кол-во повторов и повторения для n-ого упражнения во временные данные
    text = message.text.lower()
    if 'х' not in text:
        await message.answer('Напиши в формате: количество подходов x количество повторений.\nНапример: 3 x 16')
        return

    await state.update_data(**{f'exercise_{current_exercise}_sets_and_reps': text})

    # Переводим в состояние "жду вес/резинку"
    await state.set_state(AddTemplate.waiting_for_weight_or_rubber)

    await message.answer('Напиши начальный вес и/или резинку.')


@router.message(AddTemplate.waiting_for_weight_or_rubber)
async def get_exercise_weight_or_rubber(message: Message, state: FSMContext):
    # Получаем временные данные и текущий счётчик
    data = await state.get_data()
    count = data.get('exercises_count')
    current_exercise = data.get('current_exercise')
    template_name = data.get('template_name')

    # Сохраняем вес/резинку для n-ого упражнения во временные данные
    await state.update_data(**{f'exercise_{current_exercise}_weight_or_rubber': message.text})

    if current_exercise == count:
        # Получаем обновленные (после добавление веса/резинки) временные данные
        data = await state.get_data()

        # 1. Собираем список упражнений из state
        exercises = []
        for i in range(1, count + 1):
            exercises.append({
                'name': data.get(f'exercise_{i}_name'),
                'sets_and_reps': data.get(f'exercise_{i}_sets_and_reps'),
                'weight_or_rubber': data.get(f'exercise_{i}_weight_or_rubber', '')
            })

        # 2. Сохраняем в БД (передаём user_id (уникальный id в таблице user, имя шаблона и список)

        user_id = await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )

        template_id = await save_template(
            user_id=user_id,
            template_name=template_name,
            exercises=exercises
        )

        # 3. Формируем сообщение для отправки пользователю
        text = f"✅ Шаблон {template_name} успешно добавлен!\n\n"
        text += "📋 Твоя тренировка:\n"
        text += "═══════════════════\n"

        for i in range(1, count + 1):
            name = data.get(f'exercise_{i}_name')
            sets_reps = data.get(f'exercise_{i}_sets_and_reps')
            weight = data.get(f'exercise_{i}_weight_or_rubber')

            text += f"🔹 {name}\n"
            text += f"   ▫️ Подходы и повторения: {sets_reps}\n"
            text += f"   ▫️ Вес/резинка: {weight}\n"
            text += "\n"

        await message.answer(text, reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text='🏠 Вернуться в главное меню', callback_data='back_to_main')]]))

        await state.clear()
    else:
        # Текущий счётчик += 1, обновляем в state
        current_exercise += 1
        await state.update_data(current_exercise=current_exercise)

        # Устанавливаем новое состояние и переходим к следующему упражнению
        await state.set_state(AddTemplate.waiting_for_exercise_name)
        await message.answer(f'Напиши название {current_exercise}-го упражнения.')


@router.callback_query(F.data == 'view_templates')
async def view_templates(callback: CallbackQuery):
    await callback.answer('')

    # Получаем внутренний ID пользователя из БД
    user_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username
    )

    # Загружаем первую страницу (offset = 0)
    templates, total = await get_templates(user_id, offset=0)

    # Если шаблонов нет - выходим
    if not templates:
        await callback.message.edit_text(
            'У тебя пока нет шаблонов :(\n\n'
            'Добавь первый через кнопку "Добавить шаблон".',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='↩️ В меню', callback_data='templates')]
            ])
        )
        return

    # Клавиатура: каждая кнопка — один шаблон
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for t in templates:
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=f'{t["name"]}', callback_data=f'view_template_{t["id"]}|{t["name"]}')]
        )

    # Кнопки навигации
    nav_buttons = [InlineKeyboardButton(text='↩️ В меню', callback_data='templates')]

    if total > 3:  # Если есть больше 3 шаблонов, показываем "Вперёд"
        nav_buttons.append(InlineKeyboardButton(text='➡️️ Вперёд', callback_data='templates_page_1'))

    keyboard.inline_keyboard.append(nav_buttons)

    await callback.message.edit_text(
        f'📋 Твои шаблоны (всего {total}):',
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('templates_page_'))
async def paginate_templates(callback: CallbackQuery):
    await callback.answer('')

    # Извлекаем номер страницы из callback_data
    page = int(callback.data.split('_')[-1])
    offset = page * 3

    user_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username
    )

    # Загружаем шаблоны для текущей страницы
    templates, total = await get_templates(user_id, offset=offset)

    # Если шаблонов нет (такой страницы не существует)
    if not templates:
        await callback.answer('Больше шаблонов нет.', show_alert=True)
        return

    # Строим клавиатуру с шаблонами
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for t in templates:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f'{t["name"]}',
                callback_data=f'view_template_{t["id"]}|{t["name"]}'
            )
        ])

    # Кнопки навигации
    nav_buttons = []
    if page > 0:  # Если не первая страница, показываем "Назад"
        nav_buttons.append(InlineKeyboardButton(text='⬅️ Назад', callback_data=f'templates_page_{page - 1}'))
    if (page + 1) * 3 < total:  # Если есть ещё записи после текущей страницы
        nav_buttons.append(InlineKeyboardButton(text='➡️ Вперёд', callback_data=f'templates_page_{page + 1}'))

    nav_buttons.append(InlineKeyboardButton(text='↩️ В меню', callback_data='templates'))
    keyboard.inline_keyboard.append(nav_buttons)

    # Обновляем сообщение
    await callback.message.edit_text(
        f'📋 Твои шаблоны (страница {page + 1}):',
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('view_template_'))
async def view_template_detail(callback: CallbackQuery):
    await callback.answer('')

    # Разделяем строку по '|'
    parts = callback.data.split('|')
    # parts[0] — это 'view_template_5', parts[1] — имя
    template_id = int(parts[0].split('_')[-1])  # получаем число
    template_name = parts[1]  # получаем имя

    # Получаем упражнения из БД
    exercises = await get_template_exercises(template_id)

    # Формируем текст с упражнениями
    text = f"🎯 Шаблон «{template_name}»\n\n"
    text += "📋 Упражнения:\n"
    text += "═══════════════════\n"

    for idx, ex in enumerate(exercises, start=1):
        text += f"🔹 {idx}. {ex['exercise_name']}\n"
        text += f"   ▫️ Подходы и повторения: {ex['sets_and_reps']}\n"
        if ex['weight_or_rubber']:
            text += f"   ▫️ Вес/резинка: {ex['weight_or_rubber']}\n"
        text += "\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🗑️ Удалить шаблон',
                              callback_data=f'confirm_delete_template_{template_id}|{template_name}')],
        [InlineKeyboardButton(text='📋 Назад к списку шаблонов', callback_data='view_templates')],
        [InlineKeyboardButton(text='↩️ В меню шаблонов', callback_data='templates')]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith('confirm_delete_template_'))
async def confirm_delete_template(callback: CallbackQuery):
    await callback.answer('')

    parts = callback.data.split('|')
    template_id = int(parts[0].split('_')[-1])
    template_name = parts[1] if len(parts) > 1 else "Без названия"

    # Клавиатура подтверждения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✅ Да, удалить', callback_data=f'delete_template_{template_id}'),
            InlineKeyboardButton(text='❌ Нет, оставить', callback_data=f'view_template_{template_id}|{template_name}')
        ],
        [InlineKeyboardButton(text='↩️ В меню шаблонов', callback_data='templates')]
    ])

    await callback.message.edit_text(
        f"⚠️ Ты уверен, что хочешь удалить шаблон «{template_name}»?\n\nЭто действие нельзя отменить.",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith('delete_template_'))
async def delete_template(callback: CallbackQuery):
    await callback.answer('')

    template_id = int(callback.data.split('_')[-1])
    await delete_template_by_id(template_id)

    # Показываем сообщение об успешном удалении
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📋 Назад к списку шаблонов', callback_data='view_templates')],
        [InlineKeyboardButton(text='↩️ В меню шаблонов', callback_data='templates')],
    ])

    await callback.message.edit_text(
        "✅ Шаблон успешно удалён!",
        reply_markup=keyboard
    )
