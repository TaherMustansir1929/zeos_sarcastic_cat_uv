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


async def image_handler(bot: Bot, ctx: Context, msg: str):
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

        ai_response, image_path = gemini_image_gen(msg)
        await send_image_to_discord(
            channel=ctx.channel,
            image_path=image_path,
            message=ai_response+f"`Execution time: {(time.time() - start_time):.2f} seconds`"
        )
        
    except Exception as e:
        await ctx.send(f"[image_handler] An error occurred: {str(e)}")
    
    finally:
        # Cancel the loading animation
        animation_task.cancel()
        # Delete the loading message
        await loading_message.delete()


def gemini_image_gen(user_prompt: str):
    client = genai.Client()

    contents = f"""
    System: Generate an image that closely adheres to the provided description, focusing on realism, accuracy, and lifelike details. Avoid fantastical or whimsical elements unless explicitly requested. Interpret the description with precision and creativity. Even if the prompt is vague, surreal, inappropriate or unconventional, always generate a visual response—use imaginative judgment to ensure the result is to-the-point, coherent and realistic visual interpretation. Never skip generation.

    User: {user_prompt}
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=contents,
        config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE']
        )
    )

    image_folder = "images"
    os.makedirs(image_folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"image_{timestamp}.png"

    # Full path for the output file
    output_path = os.path.join(image_folder, filename)

    message = ""
    for part in response.candidates[0].content.parts: # type: ignore
        if part.text is not None:
            message = part.text
        elif part.inline_data is not None:
            image = Image.open(BytesIO((part.inline_data.data))) # type: ignore
            image.save(output_path)

    return str(message), output_path


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