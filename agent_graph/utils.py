import random
import os
from typing import cast
from pydantic import SecretStr

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq


def get_llm_model() -> tuple[str, BaseChatModel]:
    
    # 50/50 chance of Gemini and Groq
    gamble = random.randint(0, 1)
    if gamble == 0:
        return "gemini-2.0-flash", ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    
    else:
        api_key_holders = ["zeo", "taher", "bot"]
        random_idx = random.randint(0, len(api_key_holders)-1)
        
        random_api_key_holder = api_key_holders[random_idx]
        random_api_key = os.getenv(random_api_key_holder+"_GROQ_API_KEY")
        groq_api_key = cast(SecretStr, random_api_key)
        
        if not groq_api_key:
            raise ValueError("Groq API credentials not specified. API key not found.")
        
        print(f"[get_llm_model] Using {random_api_key_holder}'s API KEY")
        
        groq_models_list = [
            "deepseek-r1-distill-llama-70b",
            "qwen-qwq-32b",
            "llama-3.3-70b-versatile",
            "llama3-70b-8192",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "meta-llama/llama-4-scout-17b-16e-instruct",
        ]
        
        random_idx = random.randint(0, len(groq_models_list)-1)
        
        model_name = groq_models_list[random_idx]
           
        return model_name, ChatGroq(model=model_name, api_key=groq_api_key)

