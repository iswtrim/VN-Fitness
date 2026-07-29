import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN=os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError('BOT_TOKEN не задан в .env')

ALLOWED_USER_IDS=[]
ids_str = os.getenv('ALLOWED_USER_IDS', '')
if ids_str:
    ALLOWED_USER_IDS = [int(x.strip()) for x in ids_str.split(',') if x.strip()]

DATABASE_URL=os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError('DATABASE_URL не задан в .env')

SQLALCHEMY_DATABASE_URL=os.getenv('SQLALCHEMY_DATABASE_URL')
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError('SQLALCHEMY_DATABASE_URL не задан в .env')