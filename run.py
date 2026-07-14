import asyncio
import logging
from aiogram import Bot, Dispatcher
from middlewares import AccessMiddleware

from config import BOT_TOKEN
from handlers import start, workouts, templates, parameters

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.message.middleware(AccessMiddleware())
dp.callback_query.middleware(AccessMiddleware())


async def main():
    dp.include_router(start.router)
    dp.include_router(workouts.router)
    dp.include_router(templates.router)
    dp.include_router(parameters.router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
