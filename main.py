import os, logging, aiohttp, asyncio, io, threading
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from flask import Flask

# --- СЕКЦИЯ АНТИ-СОН (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run_web():
    # Запуск сервера на порту 10000 (стандарт для Render)
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()
# ------------------------------

TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ТВОЙ ТОПОВЫЙ НАБОР МОДЕЛЕЙ
MODELS = {
    "flux": "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
    "anime": "https://api-inference.huggingface.co/models/cagliostrolab/animagine-xl-3.1",
    "sdxl": "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
    "video_cinema": "https://api-inference.huggingface.co/models/stabilityai/stable-video-diffusion-img2vid-xt",
    "video_fast": "https://api-inference.huggingface.co/models/ali-vilab/modelscope-damo-text-to-video-hd",
    "v_dmitry": "https://api-inference.huggingface.co/models/facebook/mms-tts-rus",
    "v_elena": "https://api-inference.huggingface.co/models/vits-rus-female",
    "v_robot": "https://api-inference.huggingface.co/models/espnet/kan-bayashi_ljspeech_vits",
    "chat": "https://api-inference.huggingface.co/models/MistralAI/Mistral-7B-Instruct-v0.2"
}

headers = {"Authorization": f"Bearer {HF_TOKEN}"}
user_state = {}

async def query_hf(url, payload, is_binary=False):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload, timeout=300) as resp:
            if is_binary: return await resp.read()
            return await resp.json()

# Клавиатуры
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("🎨 Фото", "🎬 Видео", "🎵 Звук", "📊 Статус")
    return kb

def photo_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✨ FLUX.1 (Реализм)", callback_data="set_flux"),
           types.InlineKeyboardButton("🏮 Anime (Аниме)", callback_data="set_anime"))
    return kb

def video_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("🎬 Cinema HD (SVD-XT)", callback_data="set_video_cinema"),
           types.InlineKeyboardButton("📹 Fast Video (MS)", callback_data="set_video_fast"))
    return kb

# Обработчики
@dp.message_handler(commands=['start'])
async def start(m: types.Message):
    await m.answer("🚀 **Nexus AI v8.0 запущен на Render!**\nТут интернет открыт, всё будет летать.", reply_markup=main_menu())

@dp.message_handler(lambda m: m.text == "🎨 Фото")
async def p_btn(m: types.Message): await m.answer("Выбери ИИ:", reply_markup=photo_kb())

@dp.message_handler(lambda m: m.text == "🎬 Видео")
async def v_btn(m: types.Message): await m.answer("Выбери ИИ:", reply_markup=video_kb())

@dp.callback_query_handler(lambda c: c.data.startswith("set_"))
async def set_m(c: types.CallbackQuery):
    user_state[c.from_user.id] = c.data.replace("set_", "")
    await c.answer("✅")
    await bot.send_message(c.from_user.id, f"Выбран режим: {user_state[c.from_user.id].upper()}. Жду текст (English)!")

@dp.message_handler()
async def logic(m: types.Message):
    if m.text in ["🎨 Фото", "🎬 Видео", "🎵 Звук", "📊 Статус"]: return
    mode = user_state.get(m.from_user.id, "chat")
    status = await m.answer(f"⌛ Nexus AI ({mode.upper()}) работает...")
    
    try:
        if mode.startswith("video"):
            res = await query_hf(MODELS[mode], {"inputs": m.text}, is_binary=True)
            await m.reply_video(io.BytesIO(res), caption="🎬 Готово")
        elif mode in ["flux", "sdxl", "anime"]:
            res = await query_hf(MODELS[mode], {"inputs": m.text}, is_binary=True)
            await m.reply_photo(io.BytesIO(res), caption="🚀 Сгенерировано")
        elif mode.startswith("v_"):
            res = await query_hf(MODELS[mode], {"inputs": m.text}, is_binary=True)
            await m.reply_voice(io.BytesIO(res))
        else:
            res = await query_hf(MODELS["chat"], {"inputs": f"[INST]{m.text}[/INST]"})
            await status.edit_text(res[0]['generated_text'].split("]")[-1])
            return
        await status.delete()
    except:
        await status.edit_text("❌ Ошибка. Попробуй через минуту.")

if __name__ == '__main__':
    keep_alive() # Запускаем веб-сервер для Render
    executor.start_polling(dp, skip_updates=True)