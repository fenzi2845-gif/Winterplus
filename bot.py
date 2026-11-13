import os
import uuid
import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Button
from aiohttp import web

# Настройка интентов
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

CHANNEL_ID = 1570125341798965282
SERVER_IP = "winterplus.aternos.me"
SERVER_VERSION = "26.3"

# Хранилище статусов заявок в памяти (id_заявки: "pending" | "approved" | "rejected")
applications_status = {}


class AdminActionView(View):
    def __init__(self, app_id: str, minecraft_nick: str):
        super().__init__(timeout=None)
        self.app_id = app_id
        self.minecraft_nick = minecraft_nick

    @discord.ui.button(label="✅ Одобрить", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: Button):
        applications_status[self.app_id] = "approved"

        for item in self.children:
            item.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.add_field(name="Решение", value=f"✅ Одобрил {interaction.user.mention}", inline=False)

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(
            f"Заявка игрока `{self.minecraft_nick}` одобрена! На его сайте уже открылось меню.",
            ephemeral=True
        )

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: Button):
        applications_status[self.app_id] = "rejected"

        for item in self.children:
            item.disabled = True

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(name="Решение", value=f"❌ Отклонил {interaction.user.mention}", inline=False)

        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(
            f"Заявка игрока `{self.minecraft_nick}` отклонена.",
            ephemeral=True
        )


# --- ВЕБ-СЕРВЕР ДЛЯ СВЯЗИ С САЙТОМ ---

async def handle_submit(request):
    try:
        data = await request.json()
        nick = data.get("nick", "Не указан")
        age = data.get("age", "Не указан")
        about = data.get("about", "Не указано")
        discord_tag = data.get("discord", "Не указан")

        app_id = str(uuid.uuid4())
        applications_status[app_id] = "pending"

        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            channel = await bot.fetch_channel(CHANNEL_ID)

        embed = discord.Embed(
            title="📥 Новая анкета с сайта Winterplus",
            color=discord.Color.from_rgb(56, 189, 248)
        )
        embed.add_field(name="Ник в Minecraft", value=f"`{nick}`", inline=True)
        embed.add_field(name="Возраст", value=age, inline=True)
        embed.add_field(name="Discord", value=discord_tag, inline=True)
        embed.add_field(name="О себе / Планы", value=about, inline=False)
        embed.set_footer(text=f"ID заявки: {app_id[:8]}")

        await channel.send(embed=embed, view=AdminActionView(app_id, nick))

        return web.json_response({"status": "ok", "app_id": app_id}, headers=cors_headers())
    except Exception as e:
        print(f"Ошибка при приеме заявки: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500, headers=cors_headers())


async def handle_status(request):
    app_id = request.query.get("id")
    status = applications_status.get(app_id, "not_found")
    return web.json_response({"status": status}, headers=cors_headers())


async def handle_options(request):
    return web.Response(headers=cors_headers())


async def handle_root(request):
    return web.Response(text="Winterplus Bot API is running!")


def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_post("/submit", handle_submit)
    app.router.add_get("/status", handle_status)
    app.router.add_route("OPTIONS", "/submit", handle_options)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Веб-сервер запущен на порту {port}")


@bot.event
async def on_ready():
    print(f"Бот {bot.user} успешно запущен и готов принимать заявки!")


async def main():
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if not TOKEN:
        print("КРИТИЧЕСКАЯ ОШИБКА: Нет токена в переменной DISCORD_TOKEN!")
        return
    await start_web_server()
    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())