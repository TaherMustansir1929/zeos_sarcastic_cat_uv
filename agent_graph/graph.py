from dotenv import load_dotenv
from typing import Literal, Optional, cast
import discord
from discord.ext import commands
import os
import time
import aiosqlite

from langchain_core.messages import AIMessage
from langchain_core.runnables.config import RunnableConfig

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent_graph.utils import get_llm_model
from agent_graph.nodes import agent_node, tools_node
from agent_graph.routers import tools_router
from agent_graph.state import State

load_dotenv()


BASE_DIR = os.path.dirname(os.path.abspath("__file__"))
DB_DIR = os.path.join(BASE_DIR, "db", "checkpoint.sqlite")

# Initialize memory as None, will be set in agent_graph function
memory = None

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

# Compile the graph without a checkpointer for now
graph = builder.compile()


async def agent_graph(ctx: commands.Context, msg: str, handler: Literal["zeo", "assistant", "rizz", "rate", "react", "word_count", "poetry"], log: Optional[str]) -> str:
    start_time = time.time()
    
    # Initialize the memory with a running event loop
    global memory, graph
    if memory is None:
        sql_conn = await aiosqlite.connect(DB_DIR, check_same_thread=False)
        memory = AsyncSqliteSaver(conn=sql_conn)
        # Recompile the graph with the checkpointer
        graph = builder.compile(checkpointer=memory)
    
    model_name, llm = get_llm_model()
    
    config: RunnableConfig = {
        "configurable": {
            "thread_id": handler+"_thread"
        },
        "recursion_limit": 6
    }
    
    # Create state without bot and ctx objects
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
    
    #-----DEBUGGING-----
    # for msg in response["messages"][-4:]:
    #     pprint(msg)
    #     print()
    
    final_response = f"{ctx.user.mention if isinstance(ctx, discord.Interaction) else ctx.author.mention} {parsed_response} \n `Executed in {(end_time - start_time):.2f} seconds` `AI Model: {model_name}` `Tools used: {response["custom_tools_used"]}`"
    
    print(f"\nFINAL RESPONSE: {final_response}\n\n")
    
    return final_response
