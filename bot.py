"""
Instagram Downloader Bot — РАБОТАЕТ БЕЗ ЛОГИНА (как ваш download_reel.py)
"""
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import instaloader
import os
import json
import sys
from config import TELEGRAM_BOT_TOKEN

DOWNLOADS_DIR = "downloads"
RATE_LIMIT = 10
user_last_request = {}

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

# Создаём один глобальный экземпляр Instaloader (как в вашем скрипте)
L = instaloader.Instaloader(
    download_videos=True,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    quiet=True
)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("📥 Отправьте ссылку на Instagram Reels")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    current_time = message.date.timestamp()

    if user_id in user_last_request:
        elapsed = current_time - user_last_request[user_id]
        if elapsed < RATE_LIMIT:
            remaining = int(RATE_LIMIT - elapsed)
            await message.answer(f"⏳ Подождите {remaining} секунд")
            return
    user_last_request[user_id] = current_time

    text = message.text.strip()
    if "instagram.com/reel/" not in text:
        await message.answer("❌ Отправьте ссылку на reels")
        return

    try:
        shortcode = text.split("/reel/")[1].split("/")[0].split("?")[0]
    except IndexError:
        await message.answer("❌ Неверный формат ссылки")
        return

    await message.answer("⏳ Скачиваю...")

    # === ТОЧНО КАК В ВАШЕМ СКРИПТЕ ===
    try:
        # Создаём папку если нет
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
        
        # Скачиваем (синхронно, без asyncio.to_thread!)
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=DOWNLOADS_DIR)

        # Ищем .mp4
        video_path = None
        for file in os.listdir(DOWNLOADS_DIR):
            if file.endswith('.mp4'):
                video_path = os.path.join(DOWNLOADS_DIR, file)
                break

        if not video_path:
            raise Exception("Video file not found after download")

        caption = post.caption[:100] if post.caption else "Видео из Instagram"

        # Отправляем
        with open(video_path, "rb") as video_file:
            await message.answer_video(video_file, caption=caption)

        # Удаляем файл
        os.remove(video_path)

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            await message.answer("❌ Пост не найден (удалён или приватный)")
        elif "401" in error_msg:
            # Если 401 — значит кэш куков истёк, но в терминале работает — странно
            await message.answer(f"❌ Ошибка 401. Попробуйте снова через минуту.")
        else:
            await message.answer(f"❌ Ошибка: {error_msg[:100]}")
        print(f"DEBUG: {error_msg}", file=sys.stderr)

if __name__ == "__main__":
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    print("✅ Бот запущен (работает как ваш download_reel.py)")
    print("ℹ️  Использует кэш куков из ~/.config/instaloader/")
    executor.start_polling(dp, skip_updates=True)