import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class HelloWorld(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="extensionhi")
    async def say_hi(self, interaction: discord.Interaction):
        """Say hi to the bot"""
        await interaction.response.send_message(f"Hi {interaction.user.mention} from your friend the extension!")

async def setup(bot):
    await bot.add_cog(HelloWorld(bot))
    print(f"extension has been loaded!")