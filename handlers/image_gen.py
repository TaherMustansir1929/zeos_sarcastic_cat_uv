from datetime import datetime
import os
from pathlib import Path
import time
import discord
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import random
from discord.ext.commands import Context, Bot
import asyncio

from agent_graph.graph import agent_graph
from llms.dall_e_image_gen import dall_e_image_generator
from llms.gemini_image_gen import gemini_image_gen
from llms.flux_image_gen import flux_image_generator

# Animated loading messages
LOADING_MESSAGES = [
    "Thinking...",
    "Stiring up thoughts",
    "Processing...",
    "Contemplating life choices...",
    "Seeking Enlightenment...",
    "Running some code...",
]
n = len(LOADING_MESSAGES)


async def image_handler(bot: Bot, ctx: Context, model: str, msg: str):
    # Send initial loading message
    rand_idx = random.randint(0, n-1)
    loading_message = await ctx.send(LOADING_MESSAGES[rand_idx])

    # Create a task to update loading message animation
    async def update_loading():
        for _ in range(n):
            await asyncio.sleep(0.5)  # Delay between animation frames
            rand_idx = random.randint(0, n-1)
            await loading_message.edit(content=LOADING_MESSAGES[rand_idx])

    # Start the loading animation in the background
    animation_task = bot.loop.create_task(update_loading())

    try:
        start_time = time.time()

        ai_response = ""
        image_path = ""

        if model == "gemini":
            ai_response, image_path = gemini_image_gen(msg)
        elif model == "flux":
            ai_response, image_path = flux_image_generator(msg)
        elif model == "dall-e":
            ai_response, image_path = dall_e_image_generator(msg)
        
        if image_path is None:
            await ctx.reply("Failed to generate image or no valid image_path found.")
            return
        elif ai_response is None:
            ai_response = ""

        await send_image_to_discord(
            channel=ctx.channel,
            image_path=image_path,
            message=f"{ctx.author.mention} {ai_response}\n`Execution time: {(time.time() - start_time):.2f} seconds`"
        )
        
    except Exception as e:
        await ctx.reply(f"[image_handler] An error occurred: {str(e)}")
    
    finally:
        # Cancel the loading animation
        animation_task.cancel()
        # Delete the loading message
        await loading_message.delete()


async def send_image_to_discord(channel, image_path: str, message=None):
    try:
        # Check if file exists
        if not Path(image_path).exists():
            print(f"Image file not found: {image_path}")
            return False
        
        # Create discord File object
        with open(image_path, 'rb') as f:
            picture = discord.File(f)
            
            # Send the image
            if message:
                await channel.send(message, file=picture)
            else:
                await channel.send(file=picture)
        
        print(f"\nImage sent successfully to channel `{channel.name}`\nDescription: {message}\n")
        return True
        
    except discord.errors.Forbidden:
        print("Bot doesn't have permission to send messages in this channel")
        return False
    except discord.errors.HTTPException as e:
        print(f"HTTP error occurred: {e}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False