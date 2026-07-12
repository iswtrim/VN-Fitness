import asyncpg as apg
from config import DATABASE_URL


async def get_or_create_user(telegram_id: int, username: str = None):
    """
    Возвращает id пользователя из БД. Если пользователя нет — создаёт.
    """
    conn = await apg.connect(DATABASE_URL)
    try:
        user = await conn.fetchrow("SELECT id FROM users WHERE telegram_id = $1", telegram_id)
        if user:
            return user['id']
        else:
            user_id = await conn.fetchval(
                "INSERT INTO users (telegram_id, username) VALUES ($1, $2) RETURNING id",
                telegram_id, username
            )
            return user_id
    finally:
        await conn.close()


async def save_template(user_id: int, template_name: str, exercises: list):
    """
    Создаёт шаблон тренировки в БД.
    """
    conn = await apg.connect(DATABASE_URL)
    try:
        template_id = await conn.fetchval(
            "INSERT INTO templates (user_id, name) VALUES ($1, $2) RETURNING id",
            user_id, template_name
        )

        for idx, ex in enumerate(exercises):
            await conn.execute(
                """INSERT INTO template_exercises 
                   (template_id, exercise_name, sets_and_reps, weight_or_rubber, order_index)
                   VALUES ($1, $2, $3, $4, $5)""",
                template_id,
                ex['name'],
                ex['sets_and_reps'],
                ex.get('weight_or_rubber', ''),
                idx
            )

        return template_id
    finally:
        await conn.close()


async def get_templates(user_id: int, offset: int = 0):
    """
    Показывает пользователю его шаблоны (по 3 шаблона на одной странице).
    """
    conn = await apg.connect(DATABASE_URL)
    try:
        templates = await conn.fetch(
            """SELECT id, name
            FROM templates
            WHERE user_id = $1
            ORDER BY id
            LIMIT 3
            OFFSET $2""",
            user_id, offset
        )

        # Общее количество шаблонов пользователя
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM templates WHERE user_id = $1",
            user_id
        )

        return templates, total
    finally:
        await conn.close()


async def get_template_exercises(template_id: int):
    """
    Возвращает список упражнений для конкретного шаблона.
    """
    conn = await apg.connect(DATABASE_URL)
    try:
        exercises = await conn.fetch(
            """SELECT exercise_name, sets_and_reps, weight_or_rubber 
               FROM template_exercises 
               WHERE template_id = $1 
               ORDER BY order_index""",
            template_id
        )
        return exercises
    finally:
        await conn.close()


async def delete_template_by_id(template_id: int):
    """
    Удаляет шаблон и все его упражнения из БД.
    """
    conn = await apg.connect(DATABASE_URL)
    try:
        await conn.execute("DELETE FROM templates WHERE id = $1", template_id)
    finally:
        await conn.close()
