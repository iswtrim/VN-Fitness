from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import SQLALCHEMY_DATABASE_URL

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True  # если поставить True — будут видны все SQL-запросы в консоли
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False
)