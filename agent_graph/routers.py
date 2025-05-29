from typing import Literal

from langchain_core.messages import AIMessage

from agent_graph.state import State

async def tools_router(state: State) -> Literal["discord", "tools", "end"]:
    print("\nAt [tools_router] edge")
    
    last_msg = state["messages"][-1]
    
    if isinstance(last_msg, AIMessage):
        if hasattr(last_msg, "tool_calls") and len(last_msg.tool_calls) > 0:
            print("[tools_router] Routing to [tools_node]")
            return "tools"
        
    print("[tools_router] Routing to [END]")
    return "end"