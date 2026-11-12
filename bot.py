import os
import asyncio
from aiohttp import web
import discord
from discord.ext import commands

# --- НАСТРОЙКИ ---
TOKEN = os.environ.get("DISCORD_TOKEN", "")
CHANNEL_ID = 1570125341798965282  # ID вашего канала
PORT = int(os.environ.get("PORT", 8080))

# Словарь для хранения статусов заявок
APPLICATION_STATUSES = {}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

class ApplicationView(discord.ui.View):
    def __init__(self, mc_nick: str):
        super().__init__(timeout=None)
        self.mc_nick = mc_nick.strip().lower()

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.green, custom_id="accept_btn")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        APPLICATION_STATUSES[self.mc_nick] = {
            "status": "accepted",
            "link": "https://discord.gg/EHSNWvZyZv"
        }

        for item in self.children:
            item.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.add_field(name="Статус", value=f"✅ Принято администратором {interaction.user.mention}", inline=False)
        
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, custom_id="reject_btn")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        APPLICATION_STATUSES[self.mc_nick] = {
            "status": "rejected"
        }

        for item in self.children:
            item.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(name="Статус", value=f"❌ Отклонено администратором {interaction.user.mention}", inline=False)
        
        await interaction.response.edit_message(embed=embed, view=self)


# --- ВЕБ-СЕРВЕР ---

async def index_handler(request):
    return web.FileResponse('index.html')

async def handle_submit(request):
    try:
        data = await request.json()
        mc_nick = data.get('mc_nick', 'Не указан')
        discord_nick = data.get('discord_nick', 'Не указан')
        age = data.get('age', 'Не указан')
        about = data.get('about', 'Не указан')

        APPLICATION_STATUSES[mc_nick.strip().lower()] = {"status": "pending"}

        # Используем fetch_channel вместо get_channel для надежности
        try:
            channel = await bot.fetch_channel(CHANNEL_ID)
        except Exception as ex:
            print(f"[ОШИБКА] Не удалось получить канал через fetch_channel: {ex}")
            channel = None

        if not channel:
            print(f"[ОШИБКА] Бот не видит канал с ID {CHANNEL_ID}. Убедитесь, что бот есть на сервере и ID указан верно!")
            return web.json_response({"status": "error", "message": "Канал не найден"}, status=500)

        embed = discord.Embed(
            title="📥 Новая заявка на вайтлист",
            color=discord.Color.blue()
        )
        embed.add_field(name="Minecraft ник", value=mc_nick, inline=True)
        embed.add_field(name="Discord ник", value=discord_nick, inline=True)
        embed.add_field(name="Возраст", value=age, inline=True)
        embed.add_field(name="Планы на сервере", value=about, inline=False)

        view = ApplicationView(mc_nick=mc_nick)
        await channel.send(embed=embed, view=view)
        
        print(f"[УСПЕХ] Заявка от {mc_nick} успешно отправлена в Discord!")
        return web.json_response({"status": "success"})

    except Exception as e:
        print(f"[КРИТИЧЕСКАЯ ОШИБКА в handle_submit]: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def check_status(request):
    try:
        data = await request.json()
        identifier = data.get('identifier', '').strip().lower()
        status_info = APPLICATION_STATUSES.get(identifier, {"status": "pending"})
        return web.json_response(status_info)
    except Exception as e:
        return web.json_response({"status": "pending"})


# --- ЗАПУСК ---

@bot.event
async def on_ready():
    print(f"Бот {bot.user.name} успешно запущен и готов к работе!")
    try:
        channel = await bot.fetch_channel(CHANNEL_ID)
        print(f"[ПРОВЕРКА] Канал для заявок успешно найден: #{channel.name}")
    except Exception as e:
        print(f"[ПРОВЕРКА] ВНИМАНИЕ: Канал с ID {CHANNEL_ID} НЕ НАЙДЕН! Ошибка: {e}")

async def main():
    app = web.Application()
    app.router.add_get('/', index_handler)
    app.router.add_post('/api/submit', handle_submit)
    app.router.add_post('/api/check-status', check_status)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"Веб-сервер запущен на порту {PORT}")

    await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())