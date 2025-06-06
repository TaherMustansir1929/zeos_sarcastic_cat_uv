from my_prompts.langgraph_prompts import exp_prompt
from my_prompts.rizz_prompts import rizz_prompt
from my_prompts.rate_rizz_prompts import rate_prompt
from my_prompts.react_prompts import react_prompt
from my_prompts.poetry_prompts import poetry_prompt
from my_prompts.ai_prompts import ai_prompt
from my_prompts.word_count_prompts import word_count_prompt

from typing import List, cast

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, BaseMessage
from langgraph.prebuilt import ToolNode

from agent_graph.state import State
from agent_graph.my_tools import basic_tools_list


async def agent_node(state: State):
    print("\nEntering [agent_node]")
    
    model_name, base_llm = state["model"]

    if isinstance(base_llm, ChatOpenAI):
        llm_with_tools = base_llm
    else:
        llm_with_tools = base_llm.bind_tools(tools=tools_list)
    
    prompts_dict = {
        "zeo": exp_prompt,
        "rizz": rizz_prompt,
        "rate": rate_prompt,
        "poetry": poetry_prompt,
        "assistant": ai_prompt,
        "react": react_prompt,
        "word_count": word_count_prompt
    }
    
    if len(state["messages"]) > 10:
        state["messages"] = state["messages"][-10:]
    
    system_prompt = prompts_dict[state["handler"]]
    user_query = state["query"]

    state["messages"].append(SystemMessage(content=system_prompt))
    state["messages"].append(HumanMessage(content=user_query))

    response = llm_with_tools.invoke(input=state["messages"])
    
    state["messages"].append(response)
    
    # DEBUGGING
    # for msgs in state["messages"][-5:]:
    #     print(msgs, end="\n"+"-"*40+"\n")
    
    print("HANDLER => ", state["handler"])
    print("MODEL => ", model_name)
    
    return state


tools_list = basic_tools_list + []
base_tools_node = ToolNode(tools=tools_list)


async def tools_node(state: State) -> State:
    print("\nEntered [tools_node]")

    if state["tool_count"] >= 3:
        state["messages"].append(
            ToolMessage(
                content="Sorry the tool calling limit has been reached. Cannot provide any relevant information. Respond with your own deduction."
            )
        )
        return state

    if isinstance(state["messages"][-1], AIMessage):
        print(f"[tool_node] calling -> {state['messages'][-1].tool_calls}")
        state["custom_tools_used"].append(state['messages'][-1].tool_calls[0]["name"])
        
    result = cast(State, base_tools_node.invoke(state))
    state["tool_count"] += 1

    return result