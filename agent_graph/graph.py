from typing import Literal, Optional, cast
import discord
from discord.ext import commands
import os
import time

from langchain_core.messages import AIMessage
from langchain_core.runnables.config import RunnableConfig

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_graph.utils import get_llm_model
from agent_graph.nodes import agent_node, tools_node
from agent_graph.routers import tools_router
from agent_graph.state import State


BASE_DIR = os.path.dirname(os.path.abspath("__file__"))
DB_DIR = os.path.join(BASE_DIR, "db", "checkpoint.sqlite")

# Initialize memory as None, will be set in agent_graph function
memory = MemorySaver()

# Create the graph builder
builder = StateGraph(State)

AGENT = "agent_node"
TOOLS = "tools_node"

builder.add_node(AGENT, agent_node)
builder.add_node(TOOLS, tools_node)

builder.set_entry_point(AGENT)
builder.add_conditional_edges(AGENT, tools_router, {
    "tools": TOOLS,
    "end": END,
})
builder.add_edge(TOOLS, AGENT)

# Compile the graph with a memory checkpointer
graph = builder.compile(checkpointer=memory)


async def agent_graph(ctx: commands.Context, msg: str, handler: Literal["zeo", "assistant", "rizz", "rate", "react", "word_count", "poetry"], log: Optional[str]) -> str:
    start_time = time.time()
    
    model_name, llm = get_llm_model(handler=handler)
    
    config: RunnableConfig = {
        "configurable": {
            "thread_id": handler+"_thread"
        },
        "recursion_limit": 8
    }
    
    input_dict: State = {
        "messages": [],
        "handler": handler,
        "query": msg,
        "log": log,
        "tool_count": 0,
        "model": (model_name, llm),
        "custom_tools_used": []
    }
    
    response = await graph.ainvoke(input=input_dict, config=config)
    response = cast(State, response)
    
    if not isinstance(response["messages"][-1], AIMessage):
        raise ValueError("BadResponse: Latest message is not typeof: AIMessage")
    
    parsed_response = response["messages"][-1].content
    
    end_time = time.time()
    
    final_response = f"""{ctx.author.mention} {parsed_response} \n `Executed in {(end_time - start_time):.2f} seconds` `AI Model: {model_name}` {f"`Tools used: {response["custom_tools_used"]}`" if len(response["custom_tools_used"]) > 0 else ""}"""
    
    print(f"""
    USER: {msg}\n
    FINAL RESPONSE: {final_response}\n\n
    """)
    
    return final_response
