import asyncio
from datetime import datetime
import os
import random
import time
from typing import Literal
import aiofiles
import aiohttp
from discord.ext.commands import Bot, Context
import discord

from handlers.image_gen import send_image_to_discord
from llms.flux_image_edit import flux_image_edit
from llms.gemini_image_gen import gemini_image_edit

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


async def image_edit_handler(bot: Bot, ctx: Context, handler: Literal["gemini", "flux"], message: discord.Message):
    start_time = time.time()
    
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
        if message.author.bot:
            return
        
        # Initialize image_path as None
        image_path = None
        
        # Check if message has attachments
        if message.attachments:
            image_path, metadata_path = await save_discord_image_with_metadata(message)
            if image_path:
                print(f"Image saved as: {os.path.basename(str(image_path))}")
            else:
                print("Failed to save image or no valid image found.")
                await message.reply("Failed to save image or no valid image found.")
                return
        else:
            print("Please attach an image to edit.")
            await message.reply("Please attach an image to edit.")
            return
        
        if handler == "gemini":
            msg, output_path = gemini_image_edit(message.content, image_path)
        elif handler == "flux":
            msg, output_path = flux_image_edit(message.content, image_path)
        
        await send_image_to_discord(message.channel, output_path, f"{ctx.author.mention} {msg}\n`Execution time: {(time.time() - start_time):.2f} seconds`")
    
    except Exception as e:
        await ctx.send(f"[image_handler] An error occurred: {str(e)}")
    
    finally:
        # Cancel the loading animation
        animation_task.cancel()
        # Delete the loading message
        await loading_message.delete()


async def save_discord_image_with_metadata(message, save_directory="images/edit_images/saved_images"):
    image_path = await save_discord_image(message, save_directory)
    
    if image_path:
        # Create metadata file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metadata_filename = f"{timestamp}_metadata.txt"
        metadata_path = os.path.join(save_directory, metadata_filename)
        
        try:
            async with aiofiles.open(metadata_path, 'w', encoding='utf-8') as file:
                await file.write(f"Message Content: {message.content}\n")
                await file.write(f"Author: {message.author} (ID: {message.author.id})\n")
                await file.write(f"Channel: {message.channel} (ID: {message.channel.id})\n")
                await file.write(f"Server: {message.guild.name if message.guild else 'DM'}\n")
                await file.write(f"Timestamp: {message.created_at}\n")
                await file.write(f"Image File: {os.path.basename(image_path)}\n")
            
            return image_path, metadata_path
            
        except Exception as e:
            print(f"Error saving metadata: {str(e)}")
            return image_path, None
    
    return None, None


async def save_discord_image(message, save_directory="images/edit_images/saved_images"):
    
    # Create save directory if it doesn't exist
    os.makedirs(save_directory, exist_ok=True)
    
    # Check if message has attachments
    if not message.attachments:
        print("No attachments found in the message")
        return None
    
    # Find the first image attachment
    image_attachment = None
    for attachment in message.attachments:
        # Check if attachment is an image
        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
            image_attachment = attachment
            break
    
    if not image_attachment:
        print("No image attachments found in the message")
        return None
    
    try:
        # Generate filename with timestamp to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{image_attachment.filename}"
        filepath = os.path.join(save_directory, filename)
        
        # Download and save the image
        async with aiohttp.ClientSession() as session:
            async with session.get(image_attachment.url) as response:
                if response.status == 200:
                    async with aiofiles.open(filepath, 'wb') as file:
                        async for chunk in response.content.iter_chunked(8192):
                            await file.write(chunk)
                    
                    print(f"Image saved successfully: {filepath}")
                    print(f"Message content: {message.content}")
                    print(f"Author: {message.author}")
                    print(f"Channel: {message.channel}")
                    
                    return filepath
                else:
                    print(f"Failed to download image. Status code: {response.status}")
                    return None
                    
    except Exception as e:
        print(f"Error saving image: {str(e)}")
        return None