from typing import Dict, List
import json
from langchain_ollama import ChatOllama
from langchain.messages import HumanMessage, SystemMessage

# TODO: Add error handling and retries for robustness


def supervisor_query(
    model: str,
    sample_data: List[Dict],
    description: List[Dict],
) -> str:
    """Run a prompt through Ollama using LangChain integration."""
    llm = ChatOllama(
        model=model,
        temperature=0.1,
        num_predict=2048,
    )
    llm_prompt = [
        SystemMessage(
            content="You are a senior data analyst. Based on the data and high-level description provided, suggest code ideas for plots and statistics. Respond in only in JSON key-value pairs"
        ),
        HumanMessage(
            content=f"""
        Use the following format:
        {[
            {  
                "name": "code idea",
                "description": "A brief description of the code and what it would do."
            }, ...
          ]
        }
        
        Data: {json.dumps(sample_data)}
        Description: {json.dumps(description)}
        """
        ),
    ]

    try:
        response = llm.invoke(llm_prompt)
        return response.content.strip()
    except Exception as e:
        raise e
