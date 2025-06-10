# Importing libraries and modules
import asyncio
import logging
import os
from typing import cast
from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord.ext.commands import Context

from handlers.assistant import ai_handler
from handlers.channel_restriction import channel_restriction_handler
from handlers.image_edit import image_edit_handler
from handlers.image_gen import image_handler
from handlers.poetry import poetry_handler
from handlers.rate import rate_handler
from handlers.rizz import rizz_handler
from handlers.speak import speak_handler
from handlers.word_counter import word_counter_handler
from handlers.zeo import zeo_handler

# Dictionary to store chat history for each user
chat_histories_poetry = {}

# Configure discord.py logging level to INFO to avoid excessive DEBUG logs
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.WARNING)

# Configure root logger to prevent *any* default console output
root_logger = logging.getLogger()
# Remove existing handlers (like the default StreamHandler to console)
for h in root_logger.handlers[:]:
    root_logger.removeHandler(h)
# Set level high to prevent processing unless specific handlers are added
root_logger.setLevel(logging.CRITICAL)

# The FileHandler below will still work if added to a specific logger or the root logger later.

load_dotenv()
token = os.getenv("AHD_DISCORD_TOKEN")

handler_1 = logging.FileHandler(filename="ahd_discord.log", encoding="utf-8", mode="w")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    if bot.user is not None:
        print(f"we are ready to go in, {bot.user.name}")


@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server {member.name}")


@bot.command(brief="Secret command. Beware.")
async def secret(ctx):
    await ctx.send(
        "Welcome to the club twin! There are no secrets here. Just be yourself and spread positivity. Luv you gng!🥀❤"
    )


# -------------------------------------------------------------------------------------
# -----------------------------MY CUSTOM COMMANDS--------------------------------------
# -------------------------------------------------------------------------------------

# --------LANGGRAPH IMPLEMENTATION--------
from agent_graph.graph import agent_graph

@bot.command(
    name="zeo",
    brief="Ask me your stupid questions and Imma reply respectfully 😏🥀",
    help="Ask me your stupid questions and Imma reply respectfully 😏🥀",
)
@commands.cooldown(1, 30, commands.BucketType.user)
async def zeo(ctx: Context, *, msg: str):
    
    await zeo_handler(bot=bot, ctx=ctx, msg=msg)

@zeo.error
async def zeo_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(
            f"Please wait {error.retry_after:.2f} seconds before using this command again."
        )
    await ctx.reply(f"Sorry an error occurred -> {error}")


# -----------NORMAL LLM CHAT---------
@bot.command(
    brief="Talk to AI",
    help="Use this command to access an AI chatbot directly into the server.",
)
@commands.cooldown(1, 30, commands.BucketType.user)
async def ai(ctx, *, msg):
    
    await ai_handler(bot=bot, ctx=ctx, msg=msg)

@ai.error
async def ai_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(
            f"Please wait {error.retry_after:.2f} seconds before using this command again."
        )
    await ctx.reply(f"Sorry an error occurred -> {error}")


# ----------11LabsAudioCommand---------
@bot.command(
    brief="Talk to AI through 11Labs",
    help="Use this command to make your bot speak for itself.",
)
@commands.cooldown(1, 60, commands.BucketType.user)
async def speak(ctx, handler, *, msg):

    if handler not in ["zeo", "ai", "poetry"]:
        await ctx.reply("Invalid handler. Please use one of the following: zeo, ai, poetry")
        return
    
    if handler == "ai":
        handler = "assistant"

    await speak_handler(bot=bot, ctx=ctx, handler=handler, msg=msg)

@speak.error
async def speak_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(
            f"Please wait {error.retry_after:.2f} seconds before using this command again."
        )
    await ctx.reply(f"Sorry an error occurred -> {error}")


# ----------Gemini/Flux-ImageGenCommand---------
@bot.command(
    brief="Create AI images using Google Gemini or Flux.1 Kontext Pro",
    help="Use this command to create AI images using Google Gemini or Flux.1 Kontext Pro",
)
@commands.cooldown(1, 30, commands.BucketType.user)
async def image(ctx: Context, model: str, *, msg: str):

    if model not in ["gemini", "flux", "dall-e"]:
        await ctx.reply("Invalid model. Please use one of the following: gemini, flux, dall-e \nExample: !image `gemini` or `flux` or `dall-e` <Your Prompt>")
        return
    
    await image_handler(bot=bot, ctx=ctx, model=model, msg=msg)

@image.error
async def image_error(ctx: Context, error: Exception):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(
            f"Please wait {error.retry_after:.2f} seconds before using this command again."
        )
    await ctx.reply(f"Sorry an error occurred -> {error}")


#----------GeminiImageEditCommand----------
@bot.command(
    brief="Edit an image using Google Gemini",
    help="Use this command to edit an image using Google Gemini",
)
@commands.cooldown(1, 30, commands.BucketType.user)
async def edit(ctx: Context):
    
    await image_edit_handler(bot=bot, ctx=ctx, message=ctx.message)

@edit.error
async def edit_error(ctx: Context, error: Exception):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(
            f"Please wait {error.retry_after:.2f} seconds before using this command again."
        )
    await ctx.reply(f"Sorry an error occurred -> {error}")


# ---------SARCASTIC AI COMMANDS-------
@bot.command(
    brief="This command is now deprecated. Please proceed with the new command: `!zeo <Your Msg>`",
    help="This command is now deprecated. Please proceed with the new command: `!zeo <Your Msg>`",
)
@commands.cooldown(1, 15, commands.BucketType.user)
async def ask(ctx, *, msg):
    # await ask_handler(ctx, msg, chat_histories_google_sdk)
    await ctx.reply("This command is now deprecated. Please proceed with the new command: `!zeo <Your Msg>`\n Use `!help` command for further help. Thank You!")


# ---------RIZZ COMMAND-------
@bot.command(
    brief="Spawns a dirty pickup line",
    help="Use this command to generate a dirty sus pickup line",
)
@commands.cooldown(1, 15, commands.BucketType.user)
async def rizz(ctx):
    await rizz_handler(ctx)


@rizz.error
async def rizz_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            f"Please wait {error.retry_after:.2f} seconds before using this command again."
        )
    await ctx.reply(f"Sorry an error occured -> {error}")


# ---------PICKUP LINE RATING COMMAND-------
@bot.command(
    brief="Rates your pickup lines",
    help="Call this command along with your pickup line and it will rate is out of 10",
)
@commands.cooldown(1, 15, commands.BucketType.user)
async def rate(ctx, *, msg):
    await rate_handler(ctx, msg)


@rate.error
async def rate_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            f"Please wait {error.retry_after:.2f} seconds before using this command again."
        )
    await ctx.reply(f"Sorry an error occured -> {error}")


# ------WORD COUNTER FUNC-----------
@bot.event
async def on_message(message):
    await word_counter_handler(bot, message)
    await channel_restriction_handler(bot, message)


# ------------ Ping command -------------------------
@bot.command(
    brief="Checks the bot's latency.",
    help="Responds with 'Pong!' and the current latency in milliseconds.",
)
async def ping(ctx: commands.Context):
    latency = round(bot.latency * 1000 * 10)  # Latency in milliseconds
    await ctx.reply(f"Pong! 🏓 ({latency / 10}ms)")


# ----------Spam Messages-------------
@bot.command(hidden=True)
@commands.cooldown(1, 30, commands.BucketType.user)
async def spam_msg(ctx, *, msg: str):
    n = 10
    msg_arr = []

    if "?" in msg:
        msg_arr = msg.split("?")
        
        try:
            n = int(msg_arr[1].strip())
        except (IndexError, ValueError):
            n = 10
    else:
        msg_arr = [msg]

    for i in range(n):
        await ctx.send(f"[{i+1}] {msg_arr[0]}")
        await asyncio.sleep(0.25)  # Use asyncio.sleep in async function


# -----------URDU POETRY COMMAND(SPECIAL)------------------------------
@bot.command(
    brief="Get a beautiful piece of Urdu shayri",
    help="Use this command to generate a piece of Urdu poetry based on your chosen topic",
)
@commands.cooldown(1, 15, commands.BucketType.user)
async def poetry(ctx, *, msg):
    await poetry_handler(ctx, msg, chat_histories_poetry)


@poetry.error
async def poetry_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            f"Please wait {error.retry_after:.2f} seconds before using this command again."
        )
    await ctx.reply(f"Sorry an error occured -> {error}")


bot.run(str(token), log_handler=handler_1, log_level=logging.DEBUG)
