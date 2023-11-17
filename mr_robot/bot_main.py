#!/usr/bin/env python3
import os
import sys
import logging
import logging.handlers
import discord
from discord import Embed, File, app_commands
from discord.ext import commands, tasks
from discord.utils import get
import asyncio
import re
from unit_conversion import fahrenheit_to_celsius
from datetime import datetime, timedelta, timezone
import pytz
import pickle
from typing import Literal, Optional
from discord.ext.commands import Greedy, Context
from discord.app_commands import Choice

def load_env_vars(): 
    from dotenv import load_dotenv
    load_dotenv()
load_env_vars()

def load_suggestions():
    """loads the suggestions dictionary from a pickle file to memory. Effectively reloading the objects in the last state they were when the script exited"""
    if not os.path.exists('persistent_data/suggestions_log.pkl'):
        print("Creating a new suggestions dictionary...")
        return {}, 1
    with open('persistent_data/suggestions_log.pkl', 'rb') as f:
        data = pickle.load(f)
        return data['suggestions'], data['suggestion_index_counter']

def save_suggestions(suggestions, suggestion_index_counter):
    """Saves the suggestions dictionary to a pickle file. Effectively backing up the objects in memory to the disk for persistence"""
    with open('persistent_data/suggestions_log.pkl', 'wb') as f:
        pickle.dump({'suggestions': suggestions, 'suggestion_index_counter': suggestion_index_counter}, f)

suggestions, suggestion_index_counter = load_suggestions()

USER_LOGGING_AGE = timedelta(days=7)
DISCORD_API_KEY = os.environ.get('DISCORD_API_KEY')
CURRENT_BRANCH_ENV = os.environ.get('BRANCH_ENV')

CHCH_SERVER_ID = 887846613035409458
TESTING_SERVER_ID = 990935840974852126
CATS_SERVER_ID = 1065809561845497877

CHCH_ADMIN_ROLE = 887979941667405844
CHCH_HELPER_ROLE = 1015191781865947146
DEV_ADMIN_ROLE = 1132129183103975504
DEV_ADMIN_OVERRIDE_ROLE = 1138354782197776444 # for testing purposes
BACKENDPERM_USERS = [445010877297721344, 1067214271148208201] # crumpet, frodogaggins
MODPERM_ROLES = [CHCH_ADMIN_ROLE, CHCH_HELPER_ROLE, DEV_ADMIN_ROLE, DEV_ADMIN_OVERRIDE_ROLE]

# if persistent_data folder doesn't exist, create it
if not os.path.exists('./persistent_data'):
    os.makedirs('./persistent_data')
LOG_FILEHANDLER = logging.FileHandler(filename='./persistent_data/discord.log', encoding='utf-8', mode='w')
LOG_STREMHANDLER = logging.StreamHandler(sys.stderr)
discord_logger = logging.getLogger('discord') # grab the discord logger that's floating in the ether completely undescribed and only inferred in documentation
discord_logger.addHandler(LOG_FILEHANDLER) # add the file handler to the logger
discord_logger.addHandler(LOG_STREMHANDLER) # add the stream handler to the logger

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())

@bot.event
async def on_ready():
    global USER_LOGGING_CHANNEL_ID, GENERAL_CHANNEL_ID, BOT_LOG_CHANNEL_ID, CURRENT_SERVER_ID
    guild_id = bot.guilds[0].id if len(bot.guilds) == 1 else None
    CURRENT_SERVER_ID = guild_id
    if guild_id == CHCH_SERVER_ID:
        detected_server = "chch"
        GENERAL_CHANNEL_ID = 887846613035409465
        USER_LOGGING_CHANNEL_ID = 1099252679743639612
        BOT_LOG_CHANNEL_ID = 1098176177383948318
    elif guild_id == TESTING_SERVER_ID:
        detected_server = "testing"
        GENERAL_CHANNEL_ID = 1137959377362489415
        USER_LOGGING_CHANNEL_ID = 1133637838219530261
        BOT_LOG_CHANNEL_ID = 1137959377362489415
        await bot.load_extension('jishaku')
    elif guild_id == CATS_SERVER_ID:
        detected_server = "cats"
        GENERAL_CHANNEL_ID = 1150209153445417051
        USER_LOGGING_CHANNEL_ID = 1153457622960308305
        BOT_LOG_CHANNEL_ID = 1150209153445417051
    
    channel = bot.get_channel(BOT_LOG_CHANNEL_ID)
    print(f"Login in with {CURRENT_BRANCH_ENV} branch\ndetected server: {detected_server}")
    await channel.send(f"Login in with {CURRENT_BRANCH_ENV} branch\ndetected server: {detected_server}") 
    
    print(f"""Connected to server with ID: {guild_id}
        LOGGING_CHANNEL_ID set to: {USER_LOGGING_CHANNEL_ID}
        GENERAL_CHANNEL_ID set to: {GENERAL_CHANNEL_ID}
        BOT_LOG_CHANNEL_ID set to: {BOT_LOG_CHANNEL_ID}""")
    await bot.add_cog(ModCmds(bot))
    await bot.add_cog(UserCmds(bot))
    await bot.add_cog(BackendCmds(bot))
    await bot.load_extension('hello_world_extension')
    await bot.tree.sync()
    print("command tree synced")

@bot.command()
async def sync(ctx: Context, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    """
    Syncs the command tree to the specified guilds.
    Parameters:
    - ctx (Context): The invocation context.
    - guilds (Greedy[discord.Object]): The guilds to sync the command tree to.
    - spec (Optional[Literal["~", "*", "^"]]): The sync specification. Can be one of:
        - "~": Syncs the command tree to the current guild.
        - "*": Copies the global command tree to the current guild and syncs it.
        - "^": Clears the command tree for the current guild and syncs it.
        - None: Syncs the command tree globally.
    Returns:
    - None
    """
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


class ModCmds(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    # async def interaction_check(self, interaction: discord.Interaction) -> bool:
    #     # return await does_user_have_certain_role(interaction, MODPERM_ROLES)
    #     return any(role.id in MODPERM_ROLES for role in interaction.user.roles)  # only allow cmds if user 
    @app_commands.default_permissions(ban_members=True)
    @app_commands.command(name="hi")
    async def say_hi(self, interaction: discord.Interaction):
        """Say hi to the bot"""
        await interaction.response.send_message(f"Hi {interaction.user.mention}!")
    
    @app_commands.default_permissions(ban_members=True)
    @app_commands.command(name="modsend")
    async def modsend(self, interaction, channel_to_send_message: discord.TextChannel, message_to_send: str):
        """Send message as Mr Robot to a specified channel"""
        sent_message = await channel_to_send_message.send(message_to_send)
        await interaction.response.send_message(f"Message sent to #{channel_to_send_message}\nLink to message:{sent_message.jump_url}", ephemeral=True)
    
    @app_commands.default_permissions(ban_members=True)
    @app_commands.command(name="accept")
    async def accept(self, interaction: discord.Interaction, suggestion_number: int):
        """Accept a suggestion. Marks the corresponding suggestion number as accepted."""
        await update_suggestion(interaction, suggestion_number, ":white_check_mark:", "Your suggestion has been accepted! We'll try to implement this in a timely manner.")
        await interaction.response.send_message(f"Suggestion #{suggestion_number} has been accepted!", ephemeral=True)

    @app_commands.default_permissions(ban_members=True)
    @app_commands.command(name="decline")
    async def decline(self, interaction: discord.Interaction, suggestion_number: int):
        """Decline a suggestion. Marks the corresponding suggestion number as declined."""
        await update_suggestion(interaction, suggestion_number, ":x:", "Sorry, your suggestion has been declined.")
        await interaction.response.send_message(f"Suggestion #{suggestion_number} has been declined!", ephemeral=True)

    @app_commands.default_permissions(ban_members=True)    
    @app_commands.command(name="implement")
    async def implement(self, interaction: discord.Interaction, suggestion_number: int):
        """Implement a suggestion. Marks the corresponding suggestion number as implemented."""
        await update_suggestion(interaction, suggestion_number, ":tada:", "Your suggestion has been implemented!")
        await interaction.response.send_message(f"Suggestion #{suggestion_number} has been implemented!", ephemeral=True)

    @app_commands.command(name="pfp")
    async def pfp(self, interaction: discord.Interaction, user_mentioned: discord.User):
        """Get the profile picture of a user"""
        await interaction.response.send_message(user_mentioned.display_avatar.url)

    @app_commands.default_permissions(ban_members=True)    
    @app_commands.command(name="shutdown")
    async def shutdown(self, interaction: discord.Interaction):
        """Shuts down the bot. Should not restart automatically. In case something goes wrong and you need bot to go sleepy"""
        await interaction.response.send_message("Bot is shutting down...")
        await bot.close()

    @app_commands.default_permissions(ban_members=True)    
    @app_commands.command(name="load_ext")
    async def load_ext(self, interaction: discord.Interaction, ext_name: str):
        """Loads an extension"""
        await interaction.response.send_message(f"Loading extension {ext_name}...")
        await bot.load_extension(ext_name)
        await interaction.followup.send(f"Extension {ext_name} loaded!")

class BackendCmds(commands.Cog):
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # only allow cmds if user is on BACKENDPERM_USERS list, this blocks admins
        current_user_id = interaction.user.id
        return any(current_user_id == user_id for user_id in BACKENDPERM_USERS)

    @app_commands.default_permissions(manage_guild=True) # 
    @app_commands.command(name="test")
    async def say_hi(self, interaction: discord.Interaction):
        """runs a test command"""
        await interaction.response.send_message(f"Running test command!")
        await bot.load_extension('hello_world_extension')

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.command(name="blah")
    async def blah(self, interaction: discord.Interaction):
        """restarts the bot, reloading the script"""
        await interaction.response.send_message("Bot is restarting...")
        os.system('python rebooter.py')
        await bot.close()  # close the bot

    @app_commands.default_permissions(manage_guild=True)
    @app_commands.command(name="gitpull")
    async def gitpull(self, interaction: discord.Interaction):
        """pulls from git, outputs the stdout to the channel it was called from"""
        await interaction.response.send_message("Pulling from git...")
        # takes the output from stdout and stores it in a variable
        output = os.popen('git pull origin DEV').read()
        await interaction.followup.send(output)

    # @app_commands.default_permissions(manage_guild=True)
    @app_commands.command(name="set_log_level")
    @app_commands.describe(log_level="The log level to set")
    @app_commands.choices(log_level=[
        Choice(name='critical', value="CRITICAL"),
        Choice(name='error', value="ERROR"),
        Choice(name='warning', value="WARNING"),
        Choice(name='info', value="INFO"),
        Choice(name='debug', value="DEBUG"),
        Choice(name='notset', value="NOTSET"),
    ])
    async def set_log_level(self, interaction: discord.Interaction, log_level: Choice[str]):
        """sets the log level of the bot"""
        discord_logger.setLevel(log_level.value)
        await interaction.response.send_message(f"log level set to {log_level.name}")

class UserCmds(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="trading_days")
    async def trading_days(self, interaction: discord.Interaction):
        """Gives info on days shops are closed for holidays"""
        embed = Embed(title="Restricted trading days:")

        embed.add_field(name="Days Shops closed", value="Christmas Day,\nGood Friday,\nEaster Sunday.\nANZAC Day until 1.00 pm", inline=False)

        embed.add_field(name="Shops that can open on restricted trading days (some with conditions):",
                        value="Small grocery shops like dairy, green grocer,\nService station,\nPharmacy, \nTake-away,\nrestaurant, cafe,\nReal estate agency,\nGarden centre: can only open on Easter Sunday",
                        inline=False)

        embed.add_field(name="Shop providing services, rather than selling goods:",
                        value="(e.g. video rental store, hairdresser) eg. Can sell services, like haircuts. Cannot sell goods, like hair product.",
                        inline=False)

        embed.add_field(name="Shop in a premises where an exhibition or show is taking place.",
                        value="This includes markets, craft shows and stalls at these exhibitions and shows",
                        inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="suggest")
    async def suggest(self, interaction: discord.Interaction, suggestion_content: str):
        global suggestions, suggestion_index_counter
        embed = Embed(
        title=f"Suggestion #{suggestion_index_counter}",
        description=suggestion_content,
        color=0x00ff00,
        )
        embed.set_footer(text=f"From {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        suggestions_channel = get(interaction.guild.channels, name="suggestions")
        msg = await suggestions_channel.send(embed=embed)
        await interaction.response.send_message(f"Your suggestion is being submitted....") ## , ephemeral=True
        await asyncio.sleep(1)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        thread = await msg.create_thread(name=f"Suggestion #{suggestion_index_counter}")
        await thread.send(f"{interaction.user.mention} Here is the thread for your suggestion!")
        suggestions[suggestion_index_counter] = msg.id
        suggestion_index_counter += 1
        save_suggestions(suggestions, suggestion_index_counter)
        # confirmation_msg = interaction.original_response
        await interaction.edit_original_response(content=f"{interaction.user.mention} Your suggestion has been submitted!")

async def update_suggestion(ctx, suggestion_number: int, emoji: str, message: str):
    global suggestions, suggestion_index_counter
    if suggestion_number not in suggestions:
        await ctx.send(f"No suggestion found with number {suggestion_number}.")
        return
    suggestions_channel = get(ctx.guild.channels, name="suggestions")
    message_id = suggestions[suggestion_number]
    try:
        msg = await suggestions_channel.fetch_message(message_id)
        embed = msg.embeds[0]
        embed.remove_field(0)
        embed.add_field(name="Status", value=f"{emoji} {message}", inline=False)
        await msg.edit(embed=embed)
        save_suggestions(suggestions, suggestion_index_counter)
    except discord.NotFound:
        await ctx.send(f"Message with ID {message_id} not found.")
    except discord.HTTPException:
        await ctx.send("Failed to fetch or edit message.")

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return
    """ checks if the message has a likely farenheigh number (eg 120f) and replies with the converted temperature """
    msg_temperature = fahrenheit_to_celsius(msg.content)
    if msg_temperature != None:
        fahrenheit, celcius = msg_temperature
        await msg.channel.send(f"{fahrenheit}f is {celcius}c!")
    """ checks if the message is from a new user and logs it in the user-logging channel """
    if isinstance(msg.author, discord.Member) and datetime.now(timezone.utc) - msg.author.joined_at <= USER_LOGGING_AGE: # Check if the user is a Member (has a joined_at property) and if the account is newer than USER_LOGGING_AGE
        
        joined_timestamp = int(msg.author.joined_at.timestamp()) # Get the Unix timestamp of when the user joined

        embed = discord.Embed(description=f"{msg.content}\n\n*Joined: <t:{joined_timestamp}:R> ago | Channel: #{msg.channel.name}*", color=0x00ff00) # Create an embed message
        embed.set_author(name=msg.author.name, icon_url=msg.author.display_avatar.url)

        logging_channel = bot.get_channel(USER_LOGGING_CHANNEL_ID) # Get the user-logging channel
        await logging_channel.send(embed=embed) # Send the embed message to the logging channel

    await bot.process_commands(msg)


bot.load_extension('hello_world_extension')
bot.run(DISCORD_API_KEY)


