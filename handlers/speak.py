from datetime import datetime
import os
from pathlib import Path
import random
import shutil
from typing import Literal, Optional
import asyncio
from dotenv import load_dotenv
load_dotenv()

import discord
from discord.ext.commands import Context, Bot

from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

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

async def speak_handler(bot: Bot, ctx: Context, handler: Literal['zeo', 'assistant', 'rizz', 'rate', 'react', 'word_count', 'poetry'], msg: str):
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
        ai_response = await agent_graph(ctx=ctx, msg=msg, handler=handler, log="speak")
        # Clean the response
        responses = ai_response.split("%%")
        ai_response = responses[0]
        final_response = responses[1]

        audio_file = eleven_labs_api(ai_response, handler)
        await send_audio(ctx.channel, audio_file, final_response)

        # Optional - Delete the audio directory after sending the audio file
        # delete_directory("audio")

    except Exception as e:
        await ctx.send(f"[speak_handler] An error occurred: {str(e)}")
    
    finally:
        # Cancel the loading animation
        animation_task.cancel()
        # Delete the loading message
        await loading_message.delete()

    

def eleven_labs_api(text: str, handler: Optional[str]=None):
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        raise ValueError("API key is required. Either pass it as parameter or set ELEVENLABS_API_KEY environment variable.")
    audio_folder = "audio"
    os.makedirs(audio_folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"speech_{timestamp}.mp3"

    # Full path for the output file
    output_path = os.path.join(audio_folder, filename)

    elevenlabs = ElevenLabs(
        api_key=api_key,
    )

    voice_id = "nPczCjzI2devNBz1zQrb" # Brian - Default Voice
    if handler == "assistant":
        voice_id = "77aEIu0qStu8Jwv1EdhX" # Ayinde - Nigerian Accent
    elif handler == "zeo":
        voice_id = "nPczCjzI2devNBz1zQrb" # Brian - Default Voice
    elif handler == "poetry":
        voice_id = "N2lVS1w4EtoT3dr4eOWO" # Callum - Deep Voice
    
    response = elevenlabs.text_to_speech.convert(
        voice_id=voice_id,
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_multilingual_v2",
        # Optional voice settings that allow you to customize the output
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
            speed=1.0,
        ),
    )

    # Writing the audio to a file
    with open(output_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"{filename}: A new audio file was saved successfully!")
    # Return the path of the saved audio file
    return output_path


async def send_audio(channel, file_path: str, message: Optional[str]=None):
    try:
        # Convert file_path to Path object for easier handling
        audio_path = Path(file_path)
        
        # Check if file exists
        if not audio_path.exists():
            print(f"Error: Audio file '{file_path}' not found")
            return None
        
        # Check file size (Discord has 25MB limit for regular users, 100MB for Nitro)
        file_size = audio_path.stat().st_size
        max_size = 25 * 1024 * 1024  # 25MB in bytes
        
        if file_size > max_size:
            print(f"Error: File size ({file_size / (1024*1024):.2f}MB) exceeds Discord's 25MB limit")
            return None
        
        # Create Discord File object
        discord_file = discord.File(audio_path)
        
        # Send the file
        if message:
            sent_message = await channel.send(content=message, file=discord_file)
        else:
            sent_message = await channel.send(file=discord_file)
        
        print(f"Successfully sent audio file: {audio_path.name}")
        return sent_message
        
    except discord.Forbidden:
        print("Error: Bot doesn't have permission to send files in this channel")
        return None
    except discord.HTTPException as e:
        print(f"Error sending file: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def delete_directory(directory_path):
    try:
        # Convert to Path object for easier handling
        path = Path(directory_path)
        
        # Check if directory exists
        if not path.exists():
            raise FileNotFoundError(f"Directory '{directory_path}' does not exist")
        
        # Check if it's actually a directory
        if not path.is_dir():
            raise ValueError(f"'{directory_path}' is not a directory")
        
        # Delete the directory and all its contents
        shutil.rmtree(path)
        print(f"Successfully deleted directory: {directory_path}")
        return True
        
    except Exception as e:
        print(f"Error deleting directory '{directory_path}': {e}")
        return False