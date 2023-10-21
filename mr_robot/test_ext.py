import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class testingext(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="test_ext_load_hi")
    async def test_ext_load_hi(self, interaction: discord.Interaction):
        """Say hi to the bot"""
        await interaction.response.send_message(f"Hi {interaction.user.mention} from your friend the extension!")

async def setup(bot):
    await bot.add_cog(testingext(bot))
    print(f"testing_ext_cog extension has been loaded!")