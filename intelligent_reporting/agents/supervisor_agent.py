from typing import Dict, List
import json
#from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
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
    )
    llm_prompt = [
        SystemMessage(
            content=(
                "You are a senior data analyst. "
                "Your job is to generate plot and statistical analysis code ideas based solely on the provided dataset summary. "
                "Always respond with valid JSON only. "
                "Never include explanations outside JSON. "
                "The JSON must be object with a singular key-value for libraries followed by an array of objects, each with the keys: "
                "name, description, code_template."
            )
        ),
        HumanMessage(
            content=f"""
            Generate code ideas for plotting and statistical analysis.
            Output strictly in this JSON array format:
            {{
                "libraries": "all the libraries needed to run the code",
                "suggestions":[
                    {{
                        "name": "short title for the idea",
                        "description": "what the analysis or plot accomplishes",
                        "code_template": "pseudo-code showing how to implement it"
                    }}
                    ]
            }}

            Data_Summary: {json.dumps(sample_data)}
            High_Level_Description: {json.dumps(description)}
            """
        ),
    ]

    try:
        response = llm.invoke(llm_prompt)
        return response.content.strip()
    except Exception as e:
        raise e


def gpt_supervisor_query(
    sample_data: List[Dict],
    description: List[Dict],
) -> str:
    """Run a prompt through GPT using LangChain integration."""
    llm = ChatOpenAI(
        model="gspt-5-nano",
        temperature=0.1,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    llm_prompt = [
        SystemMessage(
            content=(
                "You are a senior data analyst. "
                "Your job is to generate plot and statistical analysis code ideas based solely on the provided dataset summary. "
                "Always respond with valid JSON only. "
                "Never include explanations outside JSON. "
                "The JSON must be an array of objects, each with the keys: "
                "name, description, code_template."
            )
        ),
        HumanMessage(
            content=f"""
            Generate code ideas for plotting and statistical analysis.

            Output strictly in this JSON array format:

            [
            {{
                "name": "short title for the idea",
                "description": "what the analysis or plot accomplishes",
                "code_template": "pseudo-code or a python/R template showing how to implement it"
            }}
            ]

            Data_Summary: {json.dumps(sample_data)}
            High_Level_Description: {json.dumps(description)}
            """
        ),
    ]

    try:
        response = llm.invoke(llm_prompt)
        return response.content.strip()
    except Exception as e:
        raise e