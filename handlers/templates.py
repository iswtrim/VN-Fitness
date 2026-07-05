from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from keyboards.templates_menu import templates_menu
from database.requests import save_template, get_or_create_user

router = Router()


class AddTemplate(StatesGroup):
    waiting_for_template_name = State()
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
            inline_keyboard=[[InlineKeyboardButton(text='Вернуться в главное меню', callback_data='back_to_main')]]))

        await state.clear()
    else:
        # Текущий счётчик += 1, обновляем в state
        current_exercise += 1
        await state.update_data(current_exercise=current_exercise)

        # Устанавливаем новое состояние и переходим к следующему упражнению
        await state.set_state(AddTemplate.waiting_for_exercise_name)
        await message.answer(f'Напиши название {current_exercise}-го упражнения.')
