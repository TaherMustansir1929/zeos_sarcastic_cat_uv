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

async def zeo_handler(bot: Bot, ctx: Context, msg: str):
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
        ai_response = await agent_graph(ctx=ctx, msg=msg, handler="zeo", log=None)
        await ctx.reply(ai_response)
        
    except Exception as e:
        await ctx.send(f"[zeo_handler] An error occurred: {str(e)}")
    
    finally:
        # Cancel the loading animation
        animation_task.cancel()
        # Delete the loading message
        await loading_message.delete()