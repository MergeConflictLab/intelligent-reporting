from typing import Dict, List
import json
from langchain_ollama import ChatOllama
from langchain.messages import HumanMessage, SystemMessage


def metadata_query(
    model: str,
    sample_data: List[Dict],
    schema: Dict[str, str],
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
        return response.content.strip()
    except Exception as e:
        raise e
