"""
Instagram Downloader Bot — РАБОТАЕТ БЕЗ ЛОГИНА (как ваш download_reel.py)
"""
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import instaloader
import os
import re
import shutil
import sys
from urllib.parse import urlparse
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

INSTAGRAM_MEDIA_PATHS = ("/reel/", "/p/", "/tv/")


def extract_shortcode(text: str) -> str | None:
    """Извлекает shortcode из Instagram URL (в т.ч. с query-параметрами вроде igsh)."""
    url_match = re.search(r"https?://[^\s]+", text)
    if not url_match:
        return None

    parsed = urlparse(url_match.group(0))
    if "instagram.com" not in parsed.netloc.lower():
        return None

    for media_path in INSTAGRAM_MEDIA_PATHS:
        if media_path in parsed.path:
            part = parsed.path.split(media_path, 1)[1]
            shortcode = part.split("/", 1)[0].strip()
            if shortcode:
                return shortcode

    return None


def find_first_video_file(directory: str) -> str | None:
    for root, _, files in os.walk(directory):
        for file_name in files:
            if file_name.endswith(".mp4"):
                return os.path.join(root, file_name)
    return None


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

    shortcode = extract_shortcode(message.text.strip())
    if not shortcode:
        await message.answer("❌ Отправьте корректную ссылку на Instagram reel/post")
        return

    await message.answer("⏳ Скачиваю...")

    request_dir = os.path.join(DOWNLOADS_DIR, f"request_{user_id}_{int(current_time)}")

    try:
        os.makedirs(request_dir, exist_ok=True)

        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=request_dir)

        video_path = find_first_video_file(request_dir)
        if not video_path:
            raise Exception("Video file not found after download")

        caption = post.caption[:100] if post.caption else "Видео из Instagram"

        with open(video_path, "rb") as video_file:
            await message.answer_video(video_file, caption=caption)

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            await message.answer("❌ Пост не найден (удалён или приватный)")
        elif "401" in error_msg:
            await message.answer("❌ Ошибка 401. Попробуйте снова через минуту.")
        else:
            await message.answer(f"❌ Ошибка: {error_msg[:100]}")
        print(f"DEBUG: {error_msg}", file=sys.stderr)
    finally:
        shutil.rmtree(request_dir, ignore_errors=True)


if __name__ == "__main__":
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    print("✅ Бот запущен (работает как ваш download_reel.py)")
    print("ℹ️  Использует кэш куков из ~/.config/instaloader/")
    executor.start_polling(dp, skip_updates=True)
