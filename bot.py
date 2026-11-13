import os
import discord
from discord.ext import commands
from discord.ui import View, Button

# Настройка интентов бота
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ID канала для приема заявок (уже заменен на ваш)
CHANNEL_ID = 1570125341798965282  

# Ваши ссылки и данные сервера
DISCORD_INVITE_LINK = "https://discord.gg/ваш_инвайт"  # Ссылка на ваш Discord
WEBSITE_LINK = "https://winterplus.onrender.com"       # Ссылка на сайт
SERVER_IP = "winterplus.aternos.me"                  # IP сервера
SERVER_VERSION = "26.3"                              # Версия сервера


class AdminActionView(View):
    def __init__(self, user_id: int, minecraft_nick: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.minecraft_nick = minecraft_nick

    @discord.ui.button(label="Одобрить", style=discord.ButtonStyle.green, custom_id="approve_btn")
    async def approve(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        member = guild.get_member(self.user_id)
        
        try:
            if member:
                # Отправляем игроку в ЛС сообщение об успехе
                await member.send(
                    "🎉 **Поздравляем! Ваша заявка на сервер Winterplus одобрена!**\n"
                    f"Ваш ник `{self.minecraft_nick}` добавлен в вайтлист."
                )
        except Exception:
            pass

        for item in self.children:
            item.disabled = True
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.add_field(name="Статус", value=f"✅ Одобрил {interaction.user.mention}", inline=False)
        
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"Заявка игрока `{self.minecraft_nick}` одобрена.", ephemeral=True)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.red, custom_id="reject_btn")
    async def reject(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        member = guild.get_member(self.user_id)
        
        try:
            if member:
                await member.send("❌ К сожалению, ваша заявка на сервер Winterplus была отклонена.")
        except Exception:
            pass

        for item in self.children:
            item.disabled = True
            
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(name="Статус", value=f"❌ Отклонил {interaction.user.mention}", inline=False)
        
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"Заявка игрока `{self.minecraft_nick}` отклонена.", ephemeral=True)


@bot.command()
@commands.has_permissions(administrator=True)
async def setup_whitelist(ctx):
    """Команда для отправки информационной панели (доступна администраторам)"""
    embed = discord.Embed(
        title="❄️ Вход на сервер Winterplus",
        description="Чтобы получить доступ к серверу версии **26.3**, перейдите на наш сайт и подайте заявку.",
        color=discord.Color.from_rgb(56, 189, 248)
    )
    embed.add_field(name="Сайт проекта", value=f"[Открыть сайт]({WEBSITE_LINK})", inline=False)
    embed.set_footer(text="Winterplus Community © 2026")
    
    await ctx.send(embed=embed)
    await ctx.message.delete()


@bot.event
async def on_ready():
    print(f"Бот {bot.user} успешно запущен и готов к работе!")


# Запуск бота с токеном из переменной окружения Render
TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("Ошибка: Токен Discord не найден в переменных окружения DISCORD_TOKEN!")