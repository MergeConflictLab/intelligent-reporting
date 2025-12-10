from typing import Dict, List
import json
from langchain_ollama import ChatOllama
from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
import os
from scripts.utils import json_fix, strip_code_fence

def metadata_query(
    sample_data: List[Dict],
    schema: Dict[str, str],
    description: List[Dict],
) -> str:
    """Run a prompt through Ollama using LangChain integration."""
    llm = AzureChatOpenAI(
    azure_deployment="gpt-5-nano",  # The name you gave the model in Azure AI Studio
    api_version="2024-12-01-preview",           # Check Azure for your specific version
    azure_endpoint= os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("API_KEY"),
)
    llm_prompt = [
        SystemMessage(
            content="""
You are a data analyst. 
Summarize the dataset structure based on the provided schema. 
Respond **only** in JSON with keys 'table_description' and 'columns', where 'columns' is a list of column summaries with actual text descriptions about each column.
"""
        ),
        HumanMessage(
            content=f"""
Use the following format:
{{
    "table_description": "A brief summary of the table contents.",
    "columns": [
        {{
            "name": "column_name",
            "description": "A brief description of the column."
        }},...
    ] 
}}
        
        Data: {json.dumps(sample_data)}
        Schema: {json.dumps(schema)}
        Column details: {json.dumps(description)}
        """
        ),
    ]

    try:
        response = llm.invoke(llm_prompt)
        # Normalize possible markdown/code fences and parse JSON if present
        content = strip_code_fence(response.content)
        parsed = json_fix(content)
        return parsed
    except Exception as e:
        raise e
