import os
import asyncio
from aiohttp import web
import discord
from discord.ext import commands

# --- НАСТРОЙКИ ---
TOKEN = os.environ.get("DISCORD_TOKEN", "")
PORT = int(os.environ.get("PORT", 10000))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} успешно запущен!')

# --- ВЕБ-СЕРВЕР И АПИ ---
async def index_handler(request):
    if os.path.exists("index.html"):
        return web.FileResponse("index.html")
    return web.Response(text="Winterplus Bot & Web Portal is running!")

async def handle_submit(request):
    data = await request.json()
    return web.json_response({"status": "success", "message": "Received"})

async def check_status(request):
    return web.json_response({"status": "online"})

# Запуск бота в фоновой задаче того же цикла aiohttp
async def start_bot(app):
    asyncio.create_task(bot.start(TOKEN))

app = web.Application()
app.router.add_get('/', index_handler)
app.router.add_post('/api/submit', handle_submit)
app.router.add_post('/api/check-status', check_status)

app.on_startup.append(start_bot)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=PORT)
