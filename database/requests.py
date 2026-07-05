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


async def view_templates(user_id: int):
    """
    Показывает пользователю его шаблоны
    """
    conn = await apg.connect(DATABASE_URL)
    try:
        templates_list = await conn.fetchrow
    finally:
        await conn.close()