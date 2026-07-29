from datetime import datetime

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from sqlalchemy import select

from database.engine import AsyncSessionLocal
from database.models import Template, TemplateExercise, Workout, WorkoutExercise
from keyboards.workouts_menu import workouts_menu
from database.requests import get_or_create_user

router = Router()


class AddWorkout(StatesGroup):
    choosing_template = State()
    entering_data = State()


@router.callback_query(F.data == 'workouts')
async def workouts(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Что ты хочешь сделать?', reply_markup=workouts_menu())


@router.callback_query(F.data == 'add_workout')
async def start_add_workout(callback: CallbackQuery):
    await callback.answer('')

    user_id = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username
    )

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Template).where(Template.user_id == user_id).order_by(Template.id)
        )
        templates = result.scalars().all()

    if not templates:
        await callback.message.edit_text(
            'У тебя пока нет шаблонов. Сначала создай шаблон в разделе "Шаблоны".',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='↩️ Назад', callback_data='workouts')]
            ])
        )
        return

    builder = InlineKeyboardBuilder()
    for tpl in templates:
        builder.add(InlineKeyboardButton(text=tpl.name, callback_data=f'select_template_{tpl.id}'))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text='↩️ Назад', callback_data='workouts'))

    await callback.message.edit_text(
        'Выбери шаблон, по которому будешь тренироваться:',
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith('select_template_'))
async def select_template(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')

    template_id = int(callback.data.split('_')[-1])
    await state.update_data(template_id=template_id)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TemplateExercise)
            .where(TemplateExercise.template_id == template_id)
            .order_by(TemplateExercise.order_index)
        )
        exercises = result.scalars().all()

        if not exercises:
            await callback.message.edit_text('В этом шаблоне нет упражнений.')
            return

    exercises_data = []
    for ex in exercises:
        exercises_data.append({
            'name': ex.exercise_name,
            'sets_and_reps': ex.sets_and_reps,
            'weight_or_rubber': ex.weight_or_rubber
        })

    await state.update_data(exercises=exercises_data)
    await state.update_data(current_index=0)

    await state.set_state(AddWorkout.entering_data)
    await ask_next_exercise(callback.message, state)


async def ask_next_exercise(message: Message, state: FSMContext):
    data = await state.get_data()
    exercises = data.get('exercises', [])
    current_index = data.get('current_index', 0)

    if current_index >= len(exercises):
        await save_workout(message, state)
        return

    exercise = exercises[current_index]

    text = (
        f"Упражнение {current_index + 1} из {len(exercises)}:\n"
        f"🏋️ {exercise['name']}\n\n"
        f"По умолчанию:\n"
        f"   ▫️ Подходы и повторения: {exercise['sets_and_reps']}\n"
        f"   ▫️ Вес/резинка: {exercise['weight_or_rubber'] or 'не указано'}\n\n"
        f"Напиши фактические значения через пробел:\n"
        f"`подходы повторения вес_или_резинка`\n\n"
        f"Пример: `3 16 5 кг` или `4 12 резинка 2`"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ Пропустить упражнение', callback_data='skip_exercise')],
        [InlineKeyboardButton(text='❌ Отменить тренировку', callback_data='cancel_workout')]
    ])

    await message.answer(text, reply_markup=keyboard, parse_mode='Markdown')


@router.message(AddWorkout.entering_data)
async def process_exercise_input(message: Message, state: FSMContext):
    data = await state.get_data()
    exercises = data.get('exercises', [])
    current_index = data.get('current_index', 0)

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            'Напиши хотя бы подходы и повторения.\nПример: `3 16` или `3 16 5 кг`',
            parse_mode='Markdown'
        )
        return

    # Простая проверка, что подходы и повторения — числа
    try:
        int(parts[0])
        int(parts[1])
    except ValueError:
        await message.answer('❌ Подходы и повторения должны быть числами. Например: `3 16`')
        return

    exercises[current_index]['actual_sets'] = parts[0]
    exercises[current_index]['actual_reps'] = parts[1]
    exercises[current_index]['actual_weight'] = ' '.join(parts[2:]) if len(parts) > 2 else ''
    await state.update_data(exercises=exercises)

    current_index += 1
    await state.update_data(current_index=current_index)
    await ask_next_exercise(message, state)


@router.callback_query(F.data == 'skip_exercise')
async def skip_exercise(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Упражнение пропущено.')

    data = await state.get_data()
    current_index = data.get('current_index', 0)
    exercises = data.get('exercises', [])

    exercises[current_index]['actual_sets'] = '-'
    exercises[current_index]['actual_reps'] = '-'
    exercises[current_index]['actual_weight'] = '-'
    await state.update_data(exercises=exercises)

    current_index += 1
    await state.update_data(current_index=current_index)
    await ask_next_exercise(callback.message, state)


async def save_workout(message: Message, state: FSMContext):
    data = await state.get_data()
    template_id = data.get('template_id')
    exercises_data = data.get('exercises', [])

    user_id = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username
    )

    async with AsyncSessionLocal() as session:
        new_workout = Workout(
            user_id=user_id,
            template_id=template_id,
            notes=f"Тренировка по шаблону от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        session.add(new_workout)
        await session.commit()

        for ex in exercises_data:
            actual_sets = ex.get('actual_sets', '')
            actual_reps = ex.get('actual_reps', '')
            actual_weight = ex.get('actual_weight', '')

            workout_exercise = WorkoutExercise(
                workout_id=new_workout.id,
                exercise_name=ex['name'],
                sets_and_reps=f"{actual_sets} x {actual_reps}" if actual_sets != '-' else "пропущено",
                weight_or_rubber=actual_weight or 'не указано'
            )
            session.add(workout_exercise)

        await session.commit()

    text = f"✅ Тренировка сохранена!\n\n"
    text += f"📋 Упражнения:\n"
    text += "═══════════════════\n"

    for idx, ex in enumerate(exercises_data, start=1):
        sets = ex.get('actual_sets', '-')
        reps = ex.get('actual_reps', '-')
        weight = ex.get('actual_weight', '-')
        text += f"🔹 {idx}. {ex['name']}\n"
        text += f"   ▫️ Сделано: {sets} x {reps}\n"
        text += f"   ▫️ Вес/резинка: {weight}\n"
        text += "\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📋 К тренировкам', callback_data='workouts')],
        [InlineKeyboardButton(text='🏠 В главное меню', callback_data='back_to_main')]
    ])

    await message.answer(text, reply_markup=keyboard)
    await state.clear()


@router.callback_query(F.data == 'cancel_workout')
async def cancel_workout(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Тренировка отменена.')
    await state.clear()
    await callback.message.answer(
        '❌ Добавление тренировки отменено.',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📋 К тренировкам', callback_data='workouts')],
            [InlineKeyboardButton(text='🏠 В главное меню', callback_data='back_to_main')]
        ])
    )
