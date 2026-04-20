import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN
from handlers import register_handlers
from database import init_db, mark_as_opened
from crypto import decrypt_message
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def send_capsules(bot: Bot):
    from database import conn
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE status='pending'")
    all_capsules = cursor.fetchall()

    for cap in all_capsules:
        try:
            open_time = datetime.strptime(cap[4], "%Y-%m-%d %H:%M")
            if open_time <= datetime.now():
                await bot.send_message(
                    chat_id=cap[2],
                    text=f"📬 Вам пришла капсула времени от {cap[1]}!\n\n🔐 Зашифрованное сообщение получено. Введите ключ для расшифровки."
                )
                mark_as_opened(cap[0])
                logger.info(f"Капсула {cap[0]} доставлена получателю {cap[2]}")
        except Exception as e:
            logger.error(f"Ошибка отправки капсулы {cap[0]}: {e}")

async def main():
    logger.info("Запуск бота...")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    init_db()
    register_handlers(dp)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_capsules, "interval", minutes=1, args=[bot])
    scheduler.start()
    logger.info("Планировщик запущен")

    logger.info("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())