#!/usr/bin/env python3
import os
import sys
import logging
import discord
from discord import Embed, File
from discord.ext import commands, tasks
from discord.utils import get
import asyncio
import re
from unit_conversion import fahrenheit_to_celsius
from datetime import datetime, timedelta, timezone
import pytz
import pickle

def load_env_vars(): 
    from dotenv import load_dotenv
    load_dotenv()
load_env_vars()

def load_suggestions():
    if not os.path.exists('suggestions_log.pkl'):
        print("Creating a new suggestions dictionary...")
        return {}, 1
    with open('suggestions_log.pkl', 'rb') as f:
        data = pickle.load(f)
        return data['suggestions'], data['suggestion_index_counter']

def save_suggestions(suggestions, suggestion_index_counter):
    with open('suggestions_log.pkl', 'wb') as f:
        pickle.dump({'suggestions': suggestions, 'suggestion_index_counter': suggestion_index_counter}, f)

suggestions, suggestion_index_counter = load_suggestions()

USER_LOGGING_AGE = timedelta(days=7)
LOGGING_CHANNEL_ID = 1133637838219530261
DISCORD_API_KEY = os.environ.get('DISCORD_API_KEY')
CHANNEL_ID = 1132129923771928648

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("Login Successful")
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send("HELLO BOYS, I'M BAAAAAAAACK")

@bot.command(help=f"Say's hello")
async def hello(ctx): # context, we'll use this to refer to the channel that the command was sent from
    await ctx.send("Sup yo")


@bot.command(help=f"Sends a message as the bot to a specified channel. Eg !modsend #general This is your robot overlord speaking")
async def modsend(ctx, *msg_content):
    channels_mentioned = ctx.message.channel_mentions
    if not channels_mentioned:
        await ctx.send(f"Error: You must mention/tag the channel where the message is to be sent. Please specify the channel.")
    elif len(msg_content) <= 1:
        await ctx.send(f"You did not enter a message to be sent")
    else:
        channel = channels_mentioned[0]
        await channel.send(" ".join(msg_content[1:]))
    print(type(msg_content))


@bot.command(help="Prints the profile picture for the mentioned user")
async def pfp(ctx, *args):
    user = None
    if ctx.message.mentions:  # make sure there is at least one mentioned user
        user = ctx.message.mentions[0]  # get the first mentioned user
    elif args:
        username = args[0].lower()  # get the first argument and convert to lowercase
        for attribute in ['name', 'display_name', 'global_name']:
            for user_obj in ctx.guild.members:
                if user_obj is not None:
                    attr_value = getattr(user_obj, attribute, None)
                    if attr_value is not None and attr_value.lower() == username:
                        user = user_obj
                        break
            if user is not None:
                break

    if user is not None:
        await ctx.send(str(user.avatar))
    elif args:
        await ctx.send(f"No user found with username, display name, or global name {username}.")
    else:
        await ctx.send("No user mentioned or username provided.")


@bot.command(help=f"Gives info on days shops are closed for holidays")
async def trading_days(ctx):
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

    await ctx.send(embed=embed)


@bot.command()
async def user_joined(ctx, member: discord.Member=None):
    # if no member is mentioned
    if member is None:
        await ctx.send("You must mention a member!")
        return

    # get current time
    now = datetime.now(pytz.utc)

    # get the time when member joined
    joined_at = member.joined_at

    # calculate the difference
    delta = now - joined_at

    # calculate days and hours
    days = delta.days
    hours = delta.seconds // 3600

    await ctx.send(f'{member.name} joined {days} days and {hours} hours ago.')

@bot.command(help="Submit a suggestion")
async def suggest(ctx, *, suggestion_content):
    global suggestions, suggestion_index_counter
    embed = Embed(
        title=f"Suggestion #{suggestion_index_counter}",
        description=suggestion_content,
        color=0x00ff00,
    )
    embed.set_footer(text=f"From {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    suggestions_channel = get(ctx.guild.channels, name="suggestions")
    msg = await suggestions_channel.send(embed=embed)
    await asyncio.sleep(1)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")
    thread = await msg.create_thread(name=f"Suggestion #{suggestion_index_counter}")
    await thread.send(f"{ctx.author.mention} Your suggestion has been submitted!")
    suggestions[suggestion_index_counter] = msg.id
    suggestion_index_counter += 1
    save_suggestions(suggestions, suggestion_index_counter)

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

@bot.command(help="Accept a suggestion")
async def accept(ctx, suggestion_number: int):
    await update_suggestion(ctx, suggestion_number, ":white_check_mark:", "Your suggestion has been accepted! We'll try to implement this in a timely manner.")

@bot.command(help="Decline a suggestion")
async def decline(ctx, suggestion_number: int):
    await update_suggestion(ctx, suggestion_number, ":x:", "Sorry, your suggestion has been declined.")

@bot.command(help="Mark a suggestion as implemented")
async def implement(ctx, suggestion_number: int):
    await update_suggestion(ctx, suggestion_number, ":tada:", "Your suggestion has been implemented!")

@bot.command(help="restarts the bot, reloading the script") # \n @commands.is_owner()  # This ensures only the owner can use this command
@commands.has_any_role('887979941667405844', '1015191781865947146', 'admin') # chch admin, chch helper
async def restart(ctx):
    await ctx.send("Bot is restarting...")
    os.system('python rebooter.py')  # start rebooter script
    await bot.close()  # close the bot

@bot.event
async def on_command_error(ctx, error): 
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found")
        await ctx.send_help()

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return
    
    msg_temperature = fahrenheit_to_celsius(msg.content)
    if msg_temperature != None:
        fahrenheit, celcius = msg_temperature
        await msg.channel.send(f"{fahrenheit}f is {celcius}c!")
    
    if isinstance(msg.author, discord.Member) and datetime.now(timezone.utc) - msg.author.joined_at <= USER_LOGGING_AGE: # Check if the user is a Member (has a joined_at property) and if the account is newer than USER_LOGGING_AGE
        
        joined_timestamp = int(msg.author.joined_at.timestamp()) # Get the Unix timestamp of when the user joined

        embed = discord.Embed(description=f"{msg.content}\n\n*Joined: <t:{joined_timestamp}:R> ago | Channel: #{msg.channel.name}*", color=0x00ff00) # Create an embed message
        embed.set_author(name=msg.author.name, icon_url=msg.author.display_avatar.url)

        logging_channel = bot.get_channel(LOGGING_CHANNEL_ID) # Get the logging channel
        await logging_channel.send(embed=embed) # Send the embed message to the logging channel

    await bot.process_commands(msg)


bot.run(DISCORD_API_KEY) # run and loop forever
